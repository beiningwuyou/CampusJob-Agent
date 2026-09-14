import os
from PIL import Image, ImageDraw

def create_app_icon():
    os.makedirs("build/icon.iconset", exist_ok=True)

    # 绘制基础 1024x1024 高清图标
    img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆角矩形背景 (深邃科技黑 + 金黄战备色环)
    margin = 48
    draw.rounded_rectangle(
        [margin, margin, 1024 - margin, 1024 - margin],
        radius=220,
        fill="#0f172a",
        outline="#eab308",
        width=28
    )

    # 中间醒目战备雷达/标的图形 (金黄盾徽 + 研字/Job)
    draw.ellipse([260, 260, 764, 764], outline="#ca8a04", width=16)
    draw.ellipse([370, 370, 654, 654], fill="#eab308")

    # 保存基础 PNG
    base_png = "build/icon.png"
    img.save(base_png)

    # 生成多分辨率尺寸放入 iconset
    iconset_dir = "build/icon.iconset"
    img.resize((16, 16), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_16x16.png")
    img.resize((32, 32), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_16x16@2x.png")
    img.resize((32, 32), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_32x32.png")
    img.resize((64, 64), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_32x32@2x.png")
    img.resize((128, 128), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_128x128.png")
    img.resize((256, 256), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_128x128@2x.png")
    img.resize((256, 256), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_256x256.png")
    img.resize((512, 512), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_256x256@2x.png")
    img.resize((512, 512), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_512x512.png")
    img.resize((1024, 1024), Image.Resampling.LANCZOS).save(f"{iconset_dir}/icon_512x512@2x.png")

    print("Iconset generated successfully.")

if __name__ == "__main__":
    create_app_icon()
