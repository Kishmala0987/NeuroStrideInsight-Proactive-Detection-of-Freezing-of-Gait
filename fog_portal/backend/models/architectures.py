import torch
import torch.nn as nn


class FoGDetectionModel(nn.Module):
    """
    CNN + BiLSTM + FiLM medication conditioning.
    Matches architecture used during training (dl_fog_model_best.pth).
    Input : x (B, 192, 3), m (B, 1)  medication flag 0/1
    Output: logits (B, 1)
    """

    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv1d(3, 32, 5, padding=2)
        self.bn1   = nn.BatchNorm1d(32)

        self.conv2 = nn.Conv1d(32, 64, 5, padding=2)
        self.bn2   = nn.BatchNorm1d(64)

        self.pool  = nn.MaxPool1d(2)
        self.relu  = nn.ReLU()
        self.drop  = nn.Dropout(0.3)

        # FiLM conditioning layers
        self.med_embed = nn.Linear(1, 64)
        self.gamma     = nn.Linear(64, 64)
        self.beta      = nn.Linear(64, 64)

        self.lstm = nn.LSTM(
            64, 64,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )

        self.fc = nn.Linear(128, 1)

    def forward(self, x, m):
        x = x.permute(0, 2, 1)                    # (B, 3, 192)

        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)                           # (B, 32, 96)

        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)                           # (B, 64, 48)

        # FiLM conditioning
        med   = self.med_embed(m)
        gamma = self.gamma(med).unsqueeze(-1)
        beta  = self.beta(med).unsqueeze(-1)
        x     = gamma * x + beta

        x = self.drop(x)
        x = x.permute(0, 2, 1)                    # (B, 48, 64)
        x, _ = self.lstm(x)                        # (B, 48, 128)
        x = x.mean(dim=1)                          # (B, 128)

        return self.fc(x)                          # (B, 1)


class TriggerClassificationModel(nn.Module):
    """
    CNN + BiLSTM 3-class trigger classifier.
    Matches architecture used during training (trigger_dl_model.pth).
    Input : x (B, 192, 3)
    Output: logits (B, 3)  → [StartHesitation, Turn, Walking]
    """

    def __init__(self, num_classes: int = 3):
        super().__init__()

        self.conv1 = nn.Conv1d(3, 32, kernel_size=5, padding=2)
        self.bn1   = nn.BatchNorm1d(32)

        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.bn2   = nn.BatchNorm1d(64)

        self.relu  = nn.ReLU()
        self.pool  = nn.MaxPool1d(2)
        self.drop  = nn.Dropout(0.3)

        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=64,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )

        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        x = x.permute(0, 2, 1)                    # (B, 3, 192)

        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool(x)                           # (B, 32, 96)

        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)                           # (B, 64, 48)
        x = self.drop(x)

        x = x.permute(0, 2, 1)                     # (B, 48, 64)
        x, _ = self.lstm(x)                         # (B, 48, 128)
        x = x.mean(dim=1)                           # (B, 128)

        return self.fc(x)                           # (B, 3)
