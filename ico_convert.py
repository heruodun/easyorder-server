
from PIL import Image

# 加载源图片文件
source_img = "C:\\Users\\Administrator\\Desktop\\code\\打单服务端\\logo_icon.png" # 替换为你的图片文件名

# Ico大小的列表
icon_sizes = [
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256)
]

# 通过Pillow加载图片
img = Image.open(source_img)

# 创建包含多个尺寸的ico文件
img.save('C:\\Users\\Administrator\\Desktop\\code\\打单服务端\\logo_icon.ico', format='ICO', sizes=icon_sizes)
