import matplotlib.pyplot as plt  
import numpy as np  

# 设置图表样式  
plt.style.use('seaborn')  

# 数据准备  
# baseline_value = 855.03  
# thresholds = [7000, 6000, 5000, 4000, 3000, 2000]  
# results = [878.86, 963.35, 860.40, 915.28, 919.68, 793.54]  
baseline_value = [566.86,818.49,855.03]
thresholds = [ "LetFlow/HFT-5000","LetFlow/HFT-7500"]  
results = [987.48,919.68]  

# 准备标签  
x_labels =  thresholds [:]
# x_labels.insert(0, "Baseline")  
x_labels.insert(0, "LetFlow-7500")  
x_labels.insert(0, "LetFlow-5000")  
x_labels.insert(0, "ECMP")  
results_with_baseline = baseline_value + results  

# 创建图形  
plt.figure(figsize=(12, 7))  

# 绘制柱状图  
bars = plt.bar(  
    np.arange(len(results_with_baseline)),   
    results_with_baseline,  
    color='#5B9BD5',  # 使用更柔和的蓝色  
    width=0.6,  
    edgecolor='white',  
    linewidth=1.5  
)  

# 添加基准线  
# plt.axhline(y=baseline_value, color='#FF6B6B', linestyle='--',   
#             linewidth=2, label=f'Baseline: {baseline_value:.2f}')  

# 设置y轴范围，突出差异  
plt.ylim(500, max(results_with_baseline) * 1.05)  

# 在柱子上添加数值标签  
for bar in bars:  
    height = bar.get_height()  
    plt.text(bar.get_x() + bar.get_width()/2., height,  
             f'{height:.2f}',  
             ha='center', va='bottom', fontsize=10)  

# 自定义图表  
plt.grid(True, axis='y', linestyle='--', alpha=0.7)  
plt.xlabel('Parameters', fontsize=12, labelpad=10)  
plt.ylabel('Results', fontsize=12, labelpad=10)  
plt.title('Performance Comparison with Different Flowlet Thresholds\n(Timeout: 7500)',   
          fontsize=14, pad=20)  

# 设置刻度  
plt.xticks(np.arange(len(results_with_baseline)), x_labels, fontsize=10)  
plt.yticks(fontsize=10)  

# 添加图例  
plt.legend(loc='upper right', fontsize=10)  

# 调整布局  
plt.tight_layout()  

# 显示图形  
plt.savefig('./output/all_in_one.png')