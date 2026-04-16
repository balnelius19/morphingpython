import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

MAX_IMAGES = 4
IMG_SIZE = (600, 800)  
THUMB_SIZE = (200, 200) 

class MorphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Morphing 4 visages")

        self.images = [None] * MAX_IMAGES
        self.thumbs = [None] * MAX_IMAGES
        self.weights = [0] * MAX_IMAGES

        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.control_frame = tk.Frame(self.main_container)
        self.control_frame.pack(side="left", fill="y", padx=10)

        self.buttons = []
        self.sliders = []
        self.thumb_labels = []

        for i in range(MAX_IMAGES):
            row_frame = tk.Frame(self.control_frame)
            row_frame.grid(row=i, column=0, pady=5, sticky="w")

            btn = tk.Button(row_frame, text=f"Image {i+1}", width=12, command=lambda i=i: self.load_image(i))
            btn.pack(side="top")
            self.buttons.append(btn)

            # Note: on appelle self.on_slider_move au lieu de update_weight directement
            slider = tk.Scale(row_frame, from_=0, to=100, orient="horizontal", length=150,
                              command=lambda val, i=i: self.on_slider_move(i, val))
            slider.pack(side="top")
            self.sliders.append(slider)

            thumb_label = tk.Label(row_frame, bg="gray")
            thumb_label.pack(side="top", pady=2)
            self.thumb_labels.append(thumb_label)

        self.preview_label = tk.Label(self.main_container, text="Aperçu")
        self.preview_label.pack(side="right", padx=20, pady=20, expand=True)

    def load_image(self, index):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp")])
        if not path: return

        try:
            with open(path, "rb") as f:
                chunk = f.read()
            array = np.frombuffer(chunk, dtype=np.uint8)
            img = cv2.imdecode(array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Erreur : {e}"); return

        if img is None: return

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.images[index] = cv2.resize(img, IMG_SIZE).astype(np.float32)
        
        img_thumb = cv2.resize(img, THUMB_SIZE)
        self.thumbs[index] = ImageTk.PhotoImage(Image.fromarray(img_thumb))
        self.thumb_labels[index].configure(image=self.thumbs[index])
        self.thumb_labels[index].image = self.thumbs[index]
        self.update_preview()

    def on_slider_move(self, index, val):
        val = int(val)
        self.weights[index] = val

        # --- LOGIQUE D'ÉQUILIBRAGE (Le "Push" des sliders) ---
        total = sum(self.weights)
        if total > 100:
            surplus = total - 100
            # On réduit les autres sliders proportionnellement
            for i in range(MAX_IMAGES):
                if i != index and self.weights[i] > 0:
                    reduction = min(self.weights[i], surplus)
                    self.weights[i] -= reduction
                    surplus -= reduction
                    # On met à jour visuellement le slider sans déclencher d'événement infini
                    self.sliders[i].set(self.weights[i])
                if surplus <= 0: break
        
        self.update_preview()

    def update_preview(self):
        valid_imgs = [(img, w) for img, w in zip(self.images, self.weights) if img is not None and w > 0]
        if not valid_imgs: return

        # On recalcule le total réel pour la normalisation
        total_w = sum(w for _, w in valid_imgs)
        result = np.zeros((IMG_SIZE[1], IMG_SIZE[0], 3), dtype=np.float32)

        for img, w in valid_imgs:
            result += img * (w / total_w)

        result = np.clip(result, 0, 255).astype(np.uint8)
        img_tk = ImageTk.PhotoImage(Image.fromarray(result))
        self.preview_label.configure(image=img_tk, text="")
        self.preview_label.image = img_tk

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x900")
    app = MorphApp(root)
    root.mainloop()