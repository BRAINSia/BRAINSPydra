import pickle
import sys
import pydra

path = sys.argv[1]
print(path)
f=open(path,'rb')
data=pickle.load(f)
f.close()
try:
    f = open(sys.argv[2], "a")
    print(str(data))
    print(str(data.get_output_field("stdout")))
    print(str(data.get_output_field("stderr")))
    f.write(str(data.get_output_field("stdout")))
except:
    pass
try:
    f = open(sys.argv[2], "a")
    f.write(str(data.get_output_field("stderr")))
except:
    pass
f.close()