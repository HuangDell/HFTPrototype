import os  
import re  
import numpy as np  
import matplotlib.pyplot as plt  
import seaborn as sns  
from typing import Dict, Tuple  

class BandwidthAnalyzer:  
    def __init__(self, ft_value: int, thre_value: int, version: str):  
        self.ft_value = ft_value
        self.thre_value = thre_value
        self.version = version  
        self.resources_dir = "./resources/prototype/"+version  
        self.base_filename = f"prototype_ft_{ft_value}_thre_{thre_value}_{version}"  
        self.pattern = r'65536\s+\d+\s+\d+\.\d+\s+(\d+\.\d+)'  

        if version == 'v3':  
            self.pattern = r'65536\s+\d+\s+\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)\s+\d+\.\d+\s+(\d+\.\d+)\s+(\d+\.\d+)'  
        
        os.makedirs(self.resources_dir, exist_ok=True)  
        
        self.log_file = os.path.join(self.resources_dir, f"{self.base_filename}.log")  
        self.npy_file = os.path.join(self.resources_dir, f"{self.base_filename}.npy")  
        self.png_file = os.path.join(self.resources_dir, f"{self.base_filename}.png")  

    def extract_bandwidth_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:  
        """从日志文件中提取带宽数据"""  
        average_bw = []  
        fct_99 = []  
        fct_999 = []       
        with open(self.log_file, 'r') as f:  
            content = f.read()  
            matches = re.finditer(self.pattern, content)  
            
            for match in matches:  
                average_bw.append(float(match.group(1)))  
                if self.version == 'v3':  
                    fct_99.append(float(match.group(2)))  
                    fct_999.append(float(match.group(3)))  
        
        return np.array(average_bw), np.array(fct_99), np.array(fct_999)  

    def get_statistics(self, data: np.ndarray) -> Dict:  
        """计算统计数据"""  
        if len(data) == 0:  
            return {}  
        return {  
            'mean': np.mean(data),  
            'median': np.median(data),  
            'std': np.std(data),  
            'min': np.min(data),  
            'max': np.max(data),  
            'q1': np.percentile(data, 25),  
            'q3': np.percentile(data, 75),  
            'iqr': np.percentile(data, 75) - np.percentile(data, 25)  
        }  

    def create_single_boxplot(self, ax, data: np.ndarray, stats: Dict, title: str, ylabel: str):  
        """创建单个箱线图"""  
        sns.boxplot(data=data,   
                   ax=ax,  
                   width=0.5,  
                   fliersize=5,  
                   linewidth=2,  
                   color='skyblue',  
                   flierprops={'markerfacecolor': 'red',  
                              'marker': 'o',  
                              'markeredgecolor': 'darkred'},  
                   medianprops={'color': 'red',  
                               'linewidth': 2},  
                   boxprops={'facecolor': 'skyblue',  
                            'alpha': 0.7},  
                   whiskerprops={'color': 'darkblue',  
                                'linewidth': 2},  
                   capprops={'color': 'darkblue',  
                            'linewidth': 2})  

        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')  
        ax.set_title(title, fontsize=14, pad=10)  
        
        ax.tick_params(axis='both', labelsize=10)  
        ax.spines['top'].set_visible(False)  
        ax.spines['right'].set_visible(False)  
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)  

        # 添加统计信息  
        if stats:  
            stats_text = "\n".join([  
                f"Statistical Analysis:",  
                f"━━━━━━━━━━━━━━━━━━",  
                f"Mean: {stats['mean']:.2f}",  
                f"Median: {stats['median']:.2f}",  
                f"Std Dev: {stats['std']:.2f}",  
                f"━━━━━━━━━━━━━━━━━━",  
                f"Min: {stats['min']:.2f}",  
                f"Max: {stats['max']:.2f}",  
                f"Q1: {stats['q1']:.2f}",  
                f"Q3: {stats['q3']:.2f}",  
                f"IQR: {stats['iqr']:.2f}"  
            ])  

            ax.text(1.02, 0.98, stats_text,  
                   transform=ax.transAxes,  
                   fontsize=10,  
                   verticalalignment='top',  
                   bbox=dict(facecolor='white',  
                            alpha=0.9,  
                            edgecolor='lightgray',  
                            boxstyle='round,pad=0.8'))  

    def create_boxplot(self, avg_data: np.ndarray, fct_99: np.ndarray, fct_999: np.ndarray,   
                      avg_stats: Dict, fct_99_stats: Dict, fct_999_stats: Dict):  
        """创建箱线图"""  
        sns.set_style("whitegrid")  
        sns.set_palette("husl")  

        if self.version == 'v3':  
            # 创建三个子图  
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))  
            
            # 绘制三个箱线图  
            self.create_single_boxplot(ax1, avg_data, avg_stats,   
                                     'Average Bandwidth', 'Average Bandwidth (MB/sec)')  
            self.create_single_boxplot(ax2, fct_99, fct_99_stats,   
                                     '99% FCT', '99th Percentile FCT (usec)')  
            self.create_single_boxplot(ax3, fct_999, fct_999_stats,   
                                     '99.9% FCT', '99.9th Percentile FCT (usec)')  
        else:  
            # 只创建一个图  
            fig, ax = plt.subplots(figsize=(10, 6))  
            self.create_single_boxplot(ax, avg_data, avg_stats,   
                                     'Average Bandwidth', 'Bandwidth (MB/sec)')  

        # 添加总标题  
        plt.suptitle(f'Performance Analysis\n(flowlet timeout={self.ft_value}, threshold={self.thre_value}, {self.version})',  
                    fontsize=16,  
                    fontweight='bold',  
                    y=1.05)  

        plt.tight_layout()  
        plt.savefig(self.png_file,  
                    dpi=300,  
                    bbox_inches='tight',  
                    facecolor='white',  
                    edgecolor='none')  
        plt.close()  

    def process_data(self):  
        """主处理函数"""  
        print(f"Extracting data from {self.log_file}")  
        avg_data, fct_99, fct_999 = self.extract_bandwidth_data()  

        # 计算统计数据  
        avg_stats = self.get_statistics(avg_data)  
        fct_99_stats = self.get_statistics(fct_99) if self.version == 'v3' else {}  
        fct_999_stats = self.get_statistics(fct_999) if self.version == 'v3' else {}  
        
        # 创建并保存图表  
        self.create_boxplot(avg_data, fct_99, fct_999, avg_stats, fct_99_stats, fct_999_stats)  
        
        print(f"\nAnalysis complete!")  
        print(f"Plot saved as: {self.png_file}")  
        print("\nStatistical Summary:")  
        print("\nAverage Bandwidth Stats:")  
        for key, value in avg_stats.items():  
            print(f"{key}: {value:.2f}")  
        
        if self.version == 'v3':  
            print("\n99% FCT Stats:")  
            for key, value in fct_99_stats.items():  
                print(f"{key}: {value:.2f}")  
            print("\n99.9% FCT Stats:")  
            for key, value in fct_999_stats.items():  
                print(f"{key}: {value:.2f}")  

# 使用示例  
if __name__ == "__main__":  
    ft_value = 0  
    thre_value = 0  
    version = "v3"  # 可以切换为 "v0" 测试不同版本  
    
    analyzer = BandwidthAnalyzer(ft_value, thre_value, version)  
    analyzer.process_data()