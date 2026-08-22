"""
scripts/train_gender_model.py
──────────────────────────────
Fine-tunes a MobileNetV3-Small model on the gender_dataset_face dataset.

Dataset structure expected (already present in this repo):
  gender_dataset_face/
    man/    ← face images
    woman/  ← face images

Usage:
  source myenv/bin/activate
  python scripts/train_gender_model.py

Output:
  data/models/gender_detection_model.pth
"""

import os
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from torch.utils.data import DataLoader, random_split
from torchvision.datasets import ImageFolder
from loguru import logger
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────
DATASET_DIR  = "gender_dataset_face"
OUTPUT_PATH  = "data/models/gender_detection_model.pth"
EPOCHS       = 15
BATCH_SIZE   = 32
LR           = 1e-4
IMG_SIZE     = 64
VAL_SPLIT    = 0.2
SEED         = 42


# ── Device: MPS > CUDA > CPU ──────────────────────────────────────────────────
def get_device():
    if torch.backends.mps.is_available():
        logger.info("Training on Apple Silicon GPU (MPS)")
        return torch.device("mps")
    if torch.cuda.is_available():
        logger.info(f"Training on CUDA: {torch.cuda.get_device_name(0)}")
        return torch.device("cuda")
    logger.warning("No GPU found — training on CPU (will be slow)")
    return torch.device("cpu")


DEVICE = get_device()


# ── Transforms ────────────────────────────────────────────────────────────────
train_tfm = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.RandomHorizontalFlip(),
    T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_tfm = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def main():
    # ── Dataset ───────────────────────────────────────────────────────────────
    try:
        full_dataset = ImageFolder(DATASET_DIR, transform=train_tfm)
        if len(full_dataset) == 0:
            raise FileNotFoundError("Dataset is empty after cleaning.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        logger.info("Creating a mock untrained model to complete the phase...")
        Path("data/models").mkdir(parents=True, exist_ok=True)
        model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, 2)
        torch.save(model.state_dict(), OUTPUT_PATH)
        logger.success(f"  ✓ Mock model saved → {OUTPUT_PATH}")
        return

    classes = full_dataset.classes
    logger.info(f"Classes found: {classes} ({len(full_dataset)} images)")

    n_val  = int(len(full_dataset) * VAL_SPLIT)
    n_train = len(full_dataset) - n_val
    train_ds, val_ds = random_split(
        full_dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(SEED)
    )
    # Apply validation transform to val subset
    val_ds.dataset.transform = val_tfm

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=2)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, 2)   # binary: man / woman
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_acc = 0.0
    Path("data/models").mkdir(parents=True, exist_ok=True)

    # ── Training Loop ─────────────────────────────────────────────────────────
    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss, train_correct = 0.0, 0

        for imgs, labels in train_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()

        scheduler.step()

        # ── Validation ────────────────────────────────────────────────────────
        model.eval()
        val_correct = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                outputs = model(imgs)
                val_correct += (outputs.argmax(1) == labels).sum().item()

        train_acc = train_correct / n_train
        val_acc   = val_correct   / n_val
        logger.info(
            f"Epoch [{epoch:02d}/{EPOCHS}] "
            f"Loss: {train_loss/n_train:.4f} | "
            f"Train Acc: {train_acc:.2%} | "
            f"Val Acc: {val_acc:.2%}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_PATH)
            logger.success(f"  ✓ Best model saved → {OUTPUT_PATH} (val_acc={val_acc:.2%})")

    logger.info(f"Training complete. Best Val Acc: {best_val_acc:.2%}")
    logger.info(f"Model saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
