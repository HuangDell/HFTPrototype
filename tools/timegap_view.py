import matplotlib.pyplot as plt  
import numpy as np  
from scapy.all import PcapReader, IP, UDP  
from tqdm import tqdm  
import os  
import logging  
from datetime import datetime  
from pathlib import Path  

# 配置日志  
logging.basicConfig(  
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(message)s'  
)  
logger = logging.getLogger(__name__)  

class PacketAnalyzer:  
    def __init__(self, file_name: str, source_ip='10.10.10.2', source_port=4791):  
        self.file_name = file_name  
        self.source_ip = source_ip  
        self.source_port = source_port  
        self.file_size = os.path.getsize(file_name)  
        
        # 创建缓存文件路径  
        self.cache_dir = Path('./cache')  
        self.cache_dir.mkdir(exist_ok=True)  
        
        # 使用pcap文件名、源IP和端口号创建唯一的缓存文件名  
        pcap_name = Path(file_name).stem  
        self.cache_file = self.cache_dir / f'{pcap_name}_{source_ip}_{source_port}_mac.npy'  

    def load_or_extract_mac_addresses(self) -> np.ndarray:  
        """从缓存加载或重新提取MAC地址"""  
        if self.cache_file.exists():  
            logger.info(f"Loading MAC addresses from cache: {self.cache_file}")  
            try:  
                return np.load(self.cache_file)  
            except Exception as e:  
                logger.warning(f"Error loading cache file: {e}")  
                logger.info("Falling back to extraction from pcap")  
                
        return self.extract_and_cache_mac_addresses()  

    def extract_and_cache_mac_addresses(self) -> np.ndarray:  
        """提取MAC地址并缓存结果"""  
        mac_addresses = []  
        packets_processed = 0  
        matched_packets = 0  
        
        with tqdm(total=self.file_size,   
                desc="Reading packets",   
                unit='B',   
                unit_scale=True) as pbar:  
            
            try:  
                with PcapReader(self.file_name) as pcap_reader:  
                    while True:  
                        try:  
                            packet = pcap_reader.read_packet()  
                            if packet is None:  # 文件结束  
                                logger.info("Reached end of pcap file")  
                                break  
                                
                            # 更新进度条使用实际的包大小  
                            pbar.update(len(bytes(packet)))  
                            
                            packets_processed += 1  
                            
                            if (packet.haslayer(UDP) and packet.haslayer(IP) and  
                                packet[IP].src == self.source_ip and   
                                packet[UDP].sport == self.source_port):  
                                mac_hex = packet['Ether'].src.replace(':', '')  
                                mac_addresses.append(int(mac_hex, 16))  
                                matched_packets += 1  
                                
                            if packets_processed % 100000 == 0:  
                                logger.info(f"Processed {packets_processed:,} packets, "  
                                        f"matched {matched_packets:,}")  
                                
                        except EOFError:  # 明确处理文件结束  
                            logger.info("Reached EOF")  
                            break  
                        except Exception as e:  
                            logger.warning(f"Error processing packet: {e}")  
                            continue  
                            
            except Exception as e:  
                logger.error(f"Error reading pcap file: {e}")  
                raise  
                
        logger.info(f"Finished processing {packets_processed:,} packets, "  
               f"found {matched_packets:,} matching packets")  
    
        # 转换为numpy数组并缓存  
        mac_array = np.array(mac_addresses)  
        self.save_to_cache(mac_array)  
        
        return mac_array  

    def save_to_cache(self, data: np.ndarray):  
        """保存数据到缓存文件"""  
        try:  
            np.save(self.cache_file, data)  
            logger.info(f"Saved {len(data)} MAC addresses to cache: {self.cache_file}")  
        except Exception as e:  
            logger.error(f"Error saving cache file: {e}")  

    def calculate_time_gaps(self, data: np.ndarray, min_gap=0, max_gap=20000) -> np.ndarray:  
        """计算时间间隔"""  
        logger.info("Calculating time gaps...")  
        diff = np.diff(data)  
        mask = (diff > min_gap) & (diff < max_gap)  
        filtered_diff = diff[mask]  
        logger.info(f"Found {len(filtered_diff)} valid time gaps")  
        return filtered_diff  

    def plot_time_gaps(self, data: np.ndarray, start_idx=10000, sample_size=100,   
                      output_file='time_gap_analysis.png'):  
        """绘制时间间隔分析图"""  
        logger.info(f"Plotting time gaps from index {start_idx} to {start_idx + sample_size}")  
        
        end_idx = min(start_idx + sample_size, len(data))  
        sample_data = data[start_idx:end_idx]  
        
        with plt.style.context('seaborn'):  
            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)  
            
            stats = {  
                'mean': np.mean(sample_data),  
                'std': np.std(sample_data),  
                'max': np.max(sample_data),  
                'min': np.min(sample_data)  
            }  
            
            ax.plot(sample_data, 'b-', linewidth=1, label='Time Gap')  
            ax.axhline(y=stats['mean'], color='r', linestyle='--',   
                      label=f'Mean ({stats["mean"]:.2f})')  
            
            ax.fill_between(range(len(sample_data)),  
                          stats['mean'] - stats['std'],  
                          stats['mean'] + stats['std'],  
                          color='gray', alpha=0.2,  
                          label=f'Std (±{stats["std"]:.2f})')  
            
            ax.set_title('Time Gap Analysis', pad=20)  
            ax.set_xlabel('Sample Number')  
            ax.set_ylabel('Time Gap Value')  
            ax.grid(True, linestyle='--', alpha=0.7)  
            ax.legend(loc='upper right', framealpha=0.9)  
            
            stats_text = (f'Statistics:\n'  
                         f'Max: {stats["max"]:.2f}\n'  
                         f'Min: {stats["min"]:.2f}\n'  
                         f'Mean: {stats["mean"]:.2f}\n'  
                         f'Std: {stats["std"]:.2f}')  
            
            ax.text(0.02, 0.98, stats_text,  
                   transform=ax.transAxes,  
                   verticalalignment='top',  
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))  
            
            plt.tight_layout()  
            
            try:  
                plt.savefig(output_file+f"start_{start_idx}_size_{sample_size}.png", bbox_inches='tight')  
                logger.info(f"Plot saved to {output_file}")  
            except Exception as e:  
                logger.error(f"Error saving plot: {e}")  
            finally:  
                plt.close()  

def main():  
    # 配置参数  
    file_name = './resources/ib_send_bw.pcap'  
    output_dir = './output'  
    timestamp =  file_name.split('/')[-1].split('.')[0] 
    output_file = os.path.join(output_dir, f'timegap_analysis_{timestamp}')  
    
    # 创建输出目录  
    os.makedirs(output_dir, exist_ok=True)  
    
    # 创建分析器实例  
    analyzer = PacketAnalyzer(  
        file_name=file_name,  
        source_ip='10.10.10.2',  
        source_port=4791  
    )  
    
    try:  
        logger.info("Starting packet analysis...")  
        
        # 从缓存加载或重新提取MAC地址  
        mac_addresses = analyzer.load_or_extract_mac_addresses()  
        
        # 计算时间间隔  
        time_gaps = analyzer.calculate_time_gaps(mac_addresses,min_gap=200)  
        
        # 生成图表  
        analyzer.plot_time_gaps(time_gaps, output_file=output_file,start_idx=10200,sample_size=200)  
        
        logger.info("Analysis completed successfully")  
        
    except Exception as e:  
        logger.error(f"Error during analysis: {e}")  
        raise  

if __name__ == "__main__":  
    main()