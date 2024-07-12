import pandas as pd
import numpy as np
from sklearn import metrics

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertModel, DistilBertTokenizer
import matplotlib.pyplot as plt
from wordcloud import STOPWORDS
import os, gc, re, ast, string, random, operator, warnings
from collections import defaultdict
from tqdm.auto import tqdm


warnings.filterwarnings("ignore")

# k can choose from 2, 3, 4
k = 3

MAX_LEN = 320
EPOCHS = 5
LEARNING_RATE = 1e-05
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"


def s2l(tt):
    tt = ast.literal_eval(tt)
    tt = [n for n in tt]
    return tt


def loss_fn(outputs, targets):
    return torch.nn.functional.binary_cross_entropy_with_logits(outputs, targets)


def seed_everything(seed):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# data load
class MultiLabelDataset(Dataset):
    def __init__(self, df, tokenizer, max_len, new_data=False):
        self.tokenizer = tokenizer
        self.data = df
        self.text = df.sequence
        self.new_data = new_data
        self.max_len = max_len

        if not new_data:
            self.targets = self.data.labels

    def __len__(self):
        return len(self.text)

    def __getitem__(self, index):
        text = str(self.text[index])

        inputs = self.tokenizer.encode_plus(
            text,
            None,
            add_special_tokens=True,
            max_length=self.max_len,
            pad_to_max_length=True,
            return_token_type_ids=True,
        )
        out = {
            "input_ids": torch.tensor(inputs["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(inputs["attention_mask"], dtype=torch.long),
            "token_type_ids": torch.tensor(inputs["token_type_ids"], dtype=torch.long),
        }
        if not self.new_data:
            out["targets"] = torch.tensor(self.targets[index], dtype=torch.float)

        return out


# model
class Attention(nn.Module):
    def __init__(self, d_model, nhead):
        super(Attention, self).__init__()
        self.attention = nn.MultiheadAttention(d_model, nhead)

    def forward(self, x):
        x, _ = self.attention(x, x, x)
        return x


class TextCNN(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_sizes):
        super(TextCNN, self).__init__()
        self.convs = nn.ModuleList(
            [
                nn.Conv1d(
                    in_channels, out_channels, kernel_size, padding="same", stride=1
                )
                for kernel_size in kernel_sizes
            ]
        )
        self.attention = Attention(out_channels * len(kernel_sizes), nhead=2)
        self.fc = nn.Linear(out_channels * len(kernel_sizes), 2)

    def forward(self, x):
        x = [F.relu(conv(x)) for conv in self.convs]
        x = [F.max_pool1d(conv_out, conv_out.size(2)).squeeze(2) for conv_out in x]
        x = torch.cat(x, 1)
        x = x.unsqueeze(0)  # Add batch dimension
        x = self.attention(x)
        x = x.squeeze(0)  # Remove batch dimension
        x = self.fc(x)
        return x


class Generator(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(Generator, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class DistilBertTextCNNClass(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_sizes, generator_hidden_size):
        super(DistilBertTextCNNClass, self).__init__()

        self.bert = DistilBertModel.from_pretrained("distilbert-base-uncased")
        self.text_cnn = TextCNN(in_channels, out_channels, kernel_sizes)
        self.generator = Generator(in_channels, generator_hidden_size, in_channels)

    def forward(self, input_ids, attention_mask, token_type_ids):
        output_1 = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        hidden_state = output_1[0]
        # Generate synthetic data using the generator
        gene = self.generator(hidden_state)

        # Combine original and synthetic data
        combined = hidden_state + gene

        out = combined.permute(0, 2, 1)  # Change shape for input to Conv1d
        out = self.text_cnn(out)
        return out


train_input = ""
test_input = ""
data = pd.read_csv(train_input)
data["labels"] = data.tag.map(s2l)
data.drop("tag", axis=1, inplace=True)

train_size = 0.8
train_df = data.sample(frac=train_size, random_state=42)
val_df = data.drop(train_df.index).reset_index(drop=True)
train_df.reset_index(inplace=True, drop=True)


tokenizer = DistilBertTokenizer.from_pretrained(
    "distilbert-base-uncased", truncation=True, do_lower_case=True
)
train_set = MultiLabelDataset(train_df, tokenizer, MAX_LEN)
val_set = MultiLabelDataset(val_df, tokenizer, MAX_LEN)

train_loader = DataLoader(train_set, batch_size=32, shuffle=True, num_workers=8)
val_loader = DataLoader(val_set, batch_size=32, shuffle=False, num_workers=8)

seed_everything(42)
# latent_dim is the dimension of the latent vector, you can adjust it as needed
model = DistilBertTextCNNClass(
    in_channels=768, out_channels=256, kernel_sizes=[2, 3, 4], generator_hidden_size=512
)

model.to(DEVICE)
print(f"Model on {DEVICE}")

optimizer = torch.optim.Adam(params=model.parameters(), lr=LEARNING_RATE)


def train(epoch):
    model.train()

    for _, data in tqdm(enumerate(train_loader)):
        input_ids = data["input_ids"].to(DEVICE, dtype=torch.long)
        attention_mask = data["attention_mask"].to(DEVICE, dtype=torch.long)
        token_type_ids = data["token_type_ids"].to(DEVICE, dtype=torch.long)
        targets = data["targets"].to(DEVICE, dtype=torch.float)

        outputs = model(input_ids, attention_mask, token_type_ids)
        # Generate a random latent vector 'z'
        loss = loss_fn(outputs, targets)

        if _ % 5000 == 0:
            print(f"Epoch: {epoch}, Loss: {loss.item()}")

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()


def validate():
    model.eval()

    fin_targets = []
    fin_outputs = []

    with torch.inference_mode():
        for _, data in tqdm(enumerate(val_loader, 0)):
            ids = data["input_ids"].to(DEVICE, dtype=torch.long)
            mask = data["attention_mask"].to(DEVICE, dtype=torch.long)
            token_type_ids = data["token_type_ids"].to(DEVICE, dtype=torch.long)
            targets = data["targets"].to(DEVICE, dtype=torch.float)

            outputs = model(ids, mask, token_type_ids)
            fin_targets.extend(targets.cpu().detach().numpy().tolist())
            fin_outputs.extend(torch.sigmoid(outputs).cpu().detach().numpy().tolist())

    fin_outputs = np.array(fin_outputs) >= 0.5
    accuracy = metrics.accuracy_score(fin_targets, fin_outputs)
    f1_score_micro = metrics.f1_score(fin_targets, fin_outputs, average="micro")
    f1_score_macro = metrics.f1_score(fin_targets, fin_outputs, average="macro")

    return {
        "Accuracy Score": accuracy,
        "F1 score(micro)": f1_score_micro,
        "F1 score(macro)": f1_score_macro,
    }


all_test_pred = []


def prediction():
    model.eval()

    with torch.inference_mode():
        for i, data in tqdm(enumerate(test_loader, 0)):
            ids = data["input_ids"].to(DEVICE, dtype=torch.long)
            mask = data["attention_mask"].to(DEVICE, dtype=torch.long)
            token_type_ids = data["token_type_ids"].to(DEVICE, dtype=torch.long)
            outputs = model(ids, mask, token_type_ids)
            probas = torch.sigmoid(outputs)

            all_test_pred.append(probas)
    return probas


for epoch in range(EPOCHS):
    train(epoch)
    print(validate())


# get result
test = pd.read_csv(test_input)
val_t = test.tag
test_set = MultiLabelDataset(test, tokenizer, MAX_LEN, new_data=True)
test_loader = DataLoader(test_set, batch_size=32, shuffle=False, num_workers=8)

probabilities = prediction()
all_test_pred = torch.cat(all_test_pred)
submit_df = test.copy()
submit_df.drop("sequence", inplace=True, axis=1)
label_columns = ["noncoding", "coding"]

for i, name in enumerate(label_columns):
    submit_df[name] = all_test_pred[:, i].cpu()
    submit_df.head()

submit_df.to_csv(
    f"./result.csv",
    index=False,
)
