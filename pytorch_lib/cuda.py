import torch

print(torch.__version__)
print(torch.version.cuda) # gpu
print(torch.backends.cudnn.version()) # cudnn 
print(torch.cuda.is_available())  # gpu
print(torch.cuda.device_count())
