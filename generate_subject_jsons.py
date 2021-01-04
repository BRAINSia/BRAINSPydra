from pathlib import Path
import json

p = Path("/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2")

out_json = {}
for path in p.glob("*.nii.gz"):
    print(path)
    out_json[str(path.name)]={
          "t1":             str(path), 
          "templateModel":  "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl",
          "llsModel":       "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5",
          "landmarkWeights":"/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts",
          "landmarks":      "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv",        }
print(out_json)
with open("subject_jsons.json", 'w') as outfile:
    json.dump(out_json, outfile, indent=4)    
    
