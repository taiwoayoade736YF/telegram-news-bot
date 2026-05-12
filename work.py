from PIL import Image
img = Image.open("source.png")
img.save("app.ico", sizes=[(16,16), (32,32), (48,48), (256,256)])