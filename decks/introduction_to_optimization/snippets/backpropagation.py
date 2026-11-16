import torch

a = torch.tensor(2.0, requires_grad=True)
b = torch.tensor(3.0, requires_grad=True)

f = (a + b) * b  # the forward pass records the graph
f.backward()  # the backward pass fills .grad

print(f.item(), a.grad.item(), b.grad.item())
# 15.0 3.0 8.0
