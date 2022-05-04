# from utils import generate_dataset


# total_percent = 20
# train = total_percent * 80 / 100
# valid = total_percent * 20 / 100

# generate_dataset(
#     folder_in="/home/unibna/thesis/source/dataset/train-labled",
#     train=train,
#     valid=valid,
# )


from malcon import mal_model
import utils


model_fp = "/home/unibna/thesis/source/model/2022-04-25 17_44_17.889099_checkpoint.h5"
test_mal_fp = utils.get_test_sample("/home/unibna/thesis/source/dataset/8-2-0.0")
img_np = utils.byte2img_square(test_mal_fp)

mal_model.load_model(model_fp)
mal_model.predict(img_np)