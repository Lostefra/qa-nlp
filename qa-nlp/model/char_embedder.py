import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class CharacterEmbedder(nn.Module):
    def __init__(self,
                 init_emb: torch.Tensor,
                 input_channels: int = 1,
                 output_channels: int = 600,
                 kernel_height: int = 3,
                 output_char_embedding_dimension: int = 300,
                 hidden_dim: int = 400,
                 trainable: Optional[bool] = False):
        super(CharacterEmbedder, self).__init__()

        # Create embedding layer (one extra row for padding)
        self.embedding = nn.Embedding(*init_emb.shape)
        if init_emb is not None:  # initialize weights to the embeddings provided
            self.embedding.load_state_dict({'weight': init_emb})
            self.embedding.weight.requires_grad = trainable

        input_char_embedding_dimension = init_emb.shape[1]
        self.conv_layer = nn.Conv2d(in_channels=input_channels,
                                    out_channels=output_channels,
                                    kernel_size=(kernel_height, input_char_embedding_dimension),
                                    stride=1,
                                    padding=(1, 0))

        self.fc1 = nn.Linear(in_features=output_channels, out_features=hidden_dim)
        self.fc2 = nn.Linear(in_features=hidden_dim, out_features=output_char_embedding_dimension)

        self.char_emb_dim = output_char_embedding_dimension

    def forward(self, x):
        # (batch_size, seq_len, word_len)
        bs = x.shape[0]
        x = self.embedding(x)  # (batch_size, seq_len, word_len, input_char_embedding_dim)
        # (batch_size * seq_len, word_len, input_char_embedding_dim)
        x = x.view(x.shape[0] * x.shape[1], x.shape[2], x.shape[3])
        x = x.unsqueeze(1)  # (batch_size, input_channel = 1, word_length, input_char_embedding_dim)

        x = self.conv_layer(x)
        x = x.squeeze(3)
        x = F.relu(x)
        x = F.max_pool1d(x, kernel_size=x.shape[2])
        x = x.squeeze(2)

        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)

        # (batch_size, output_char_embedding_dim)
        x = x.unsqueeze(1)  # (batch_size, 1, output_char_embedding_dim)
        return x.view(bs, -1, x.shape[2])  # (batch_size, seq_len, output_char_embedding_dim)
