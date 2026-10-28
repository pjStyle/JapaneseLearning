from japanese_learning.inference import LocalModel
from japanese_learning.prompts import GENERATOR, ASSESSOR, generation_data, assessment_data

model = LocalModel()
for system, data in [
    (GENERATOR, generation_data(["雨", "電車", "傘"], "N3")),
    (ASSESSOR, assessment_data("I went to the library yesterday.", "昨日、図書館に行きました。", "N3")),
]:
    print("RAW:", repr(model.complete([{"role": "system", "content": system}, {"role": "user", "content": data}])), flush=True)
