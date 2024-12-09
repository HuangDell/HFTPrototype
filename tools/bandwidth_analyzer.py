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
        self.pattern = r'65536\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)'

        if version == 'v3':
            self.pattern = r'2\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)'
            
        
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
            matches = re.finditer(self.pattern, content)
            
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
        """创建美化版箱线图和统计信息"""  
        # 设置 seaborn 样式  
        sns.set_style("whitegrid")  # 设置网格背景样式  
        sns.set_palette("husl")     # 设置调色板  
        
        # 创建图形和轴对象  
        fig, ax = plt.subplots(figsize=(10, 6))  
        
        # 创建美化的箱线图  
        sns.boxplot(data=data,   
                    ax=ax,  
                    width=0.5,                # 设置箱体宽度  
                    fliersize=5,              # 设置异常值点的大小  
                    linewidth=2,              # 设置线条宽度  
                    color='skyblue',          # 设置箱体颜色  
                    flierprops={'markerfacecolor': 'red',    # 异常值点的颜色  
                            'marker': 'o',                 # 异常值点的形状  
                            'markeredgecolor': 'darkred'}, # 异常值点边框颜色  
                    medianprops={'color': 'red',             # 中位数线的颜色  
                                'linewidth': 2},              # 中位数线的宽度  
                    boxprops={'facecolor': 'skyblue',        # 箱体填充颜色  
                            'alpha': 0.7},                   # 箱体透明度  
                    whiskerprops={'color': 'darkblue',       # 须线颜色  
                                'linewidth': 2},             # 须线宽度  
                    capprops={'color': 'darkblue',           # 须线末端颜色  
                            'linewidth': 2})                 # 须线末端宽度  
        
        ax.set_ylabel('Bandwidth (MB/sec)',   
                    fontsize=12,   
                    fontweight='bold')  
        
        # 美化坐标轴  
        ax.tick_params(axis='both', labelsize=10)  
        ax.spines['top'].set_visible(False)    # 隐藏上边框  
        ax.spines['right'].set_visible(False)  # 隐藏右边框  
        
        # 添加水平参考线  
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)  
        
        # 准备统计信息文本  
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
        
        # 在右上角添加美化的文本框  
        ax.text(0.80, 0.98, stats_text,  
                transform=ax.transAxes,  
                fontsize=10,  
                verticalalignment='top',  
                horizontalalignment='left',  
                bbox=dict(facecolor='white',  
                        alpha=0.9,  
                        edgecolor='lightgray',  
                        boxstyle='round,pad=0.8'))  
        
        # 添加主标题  
        plt.suptitle(f'Bandwidth Performance Analysis\n(flowlet timeout={self.ft_value}, threshold={self.thre_value}, {self.version})',  
                    fontsize=16,  
                    fontweight='bold',  
                    y=1.05)  
        
        # 调整布局  
        plt.tight_layout()  
        # plt.subplots_adjust(right=0.85, top=0.88)  
        
        # 保存高质量图片  
        plt.savefig(self.png_file,   
                    dpi=300,   
                    bbox_inches='tight',  
                    facecolor='white',  
                    edgecolor='none')  
        plt.close()  

    def process_data(self):
        """主处理函数"""
        print(f"Extracting data from {self.log_file}")
        peak_bw, average_bw = self.extract_bandwidth_data()
        # 保存数据

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

# 设置参数
ft_value = 7500 # 可以根据需要修改
thre_value = 0  # 可以根据需要修改
version = "v0"  # 可以根据需要修改

# 使用示例
if __name__ == "__main__":
    
    # 创建分析器实例并处理数据
    analyzer = BandwidthAnalyzer(ft_value, thre_value, version)
    analyzer.process_data()