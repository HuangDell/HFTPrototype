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
        self.resources_dir = "./resources/prototype"
        self.base_filename = f"prototype_ft_{ft_value}_thre_{thre_value}_{version}"
        
        # 确保目录存在
        os.makedirs(self.resources_dir, exist_ok=True)
        
        # 文件路径
        self.log_file = os.path.join(self.resources_dir, f"{self.base_filename}.log")
        self.npy_file = os.path.join(self.resources_dir, f"{self.base_filename}.npy")
        self.png_file = os.path.join(self.resources_dir, f"{self.base_filename}.png")

    def extract_bandwidth_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """从日志文件中提取带宽数据"""
        peak_bw = []
        average_bw = []
        
        with open(self.log_file, 'r') as f:
            content = f.read()
            pattern = r'65536\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                peak_bw.append(float(match.group(1)))
                average_bw.append(float(match.group(2)))
        
        return np.array(peak_bw), np.array(average_bw)

    def get_statistics(self, data: np.ndarray) -> Dict:
        """计算统计数据"""
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

    def create_boxplot(self, data: np.ndarray, stats: Dict):
        """创建箱线图和统计信息"""
        plt.figure(figsize=(12, 8))
        
        # 创建两个子图
        gs = plt.GridSpec(1, 2, width_ratios=[2, 1])
        
        # 箱线图
        ax1 = plt.subplot(gs[0])
        sns.boxplot(data=data, ax=ax1)
        ax1.set_title('Bandwidth Average Distribution')
        ax1.set_ylabel('MB/sec')
        
        # 统计信息
        ax2 = plt.subplot(gs[1])
        ax2.axis('off')
        stats_text = "\n".join([
            f"Statistical Analysis:",
            f"Mean: {stats['mean']:.2f}",
            f"Median: {stats['median']:.2f}",
            f"Std Dev: {stats['std']:.2f}",
            f"Min: {stats['min']:.2f}",
            f"Max: {stats['max']:.2f}",
            f"Q1: {stats['q1']:.2f}",
            f"Q3: {stats['q3']:.2f}",
            f"IQR: {stats['iqr']:.2f}"
        ])
        ax2.text(0, 0.7, stats_text, fontsize=10, verticalalignment='top')
        
        # 添加标题
        plt.suptitle(f'Bandwidth Analysis (ft={self.ft_value}, thre={self.thre_value}, {self.version})')
        
        # 保存图片
        plt.tight_layout()
        plt.savefig(self.png_file, dpi=300, bbox_inches='tight')
        plt.close()

    def process_data(self):
        """主处理函数"""
        # 检查是否存在npy文件
        if os.path.exists(self.npy_file):
            print(f"Loading existing data from {self.npy_file}")
            data = np.load(self.npy_file, allow_pickle=True).item()
            peak_bw = data['peak_bw']
            average_bw = data['average_bw']
        else:
            print(f"Extracting data from {self.log_file}")
            peak_bw, average_bw = self.extract_bandwidth_data()
            # 保存数据
            np.save(self.npy_file, {'peak_bw': peak_bw, 'average_bw': average_bw})

        # 计算统计数据
        stats = self.get_statistics(average_bw)
        
        # 创建并保存图表
        self.create_boxplot(average_bw, stats)
        
        print(f"\nAnalysis complete!")
        print(f"Data file: {self.npy_file}")
        print(f"Plot saved as: {self.png_file}")
        print("\nStatistical Summary:")
        for key, value in stats.items():
            print(f"{key}: {value:.2f}")

# 使用示例
if __name__ == "__main__":
    # 设置参数
    ft_value = 1
    thre_value = 2
    version = "v1"
    
    # 创建分析器实例并处理数据
    analyzer = BandwidthAnalyzer(ft_value, thre_value, version)
    analyzer.process_data()