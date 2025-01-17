## @file
# UNFINISHED Workflow file for AL training
# by Anna Andraszek

import toc_classification
import fig_classification
import heading_id_toc
import marginals_classification
import page_identification
import page_extraction
import heading_id_intext
import heading_classification
import paths
import glob
import re
import os
import time
import matplotlib.pyplot as plt
import active_learning

#def check_report_criteria():  # check if going to use restruct page info file
    # check if reportid is correct type: not WELCOM
                    #   is not QLD Mining Journal: QUEENSLAND GOVERNMENT MINING JOURNAL not in Report Title
                    #   no restriction for age, no other restrictions
    # only need to do this on the first training set




def save_dataset(df, name):
    path = paths.get_dataset_path(name)
    if not os.path.exists(paths.dataset_path + '/' + paths.dataset_version):
        os.mkdir(paths.dataset_path + '/' + paths.dataset_version)
    if not os.path.exists(path):
        df.to_csv(path, index=False)
    else:
        print('Dataset already exists here. To prevent overwriting annotation, delete it manually first.')


def create_training_sets_pt1(): # creating of training sets, up to their annotation
    toc_df = toc_classification.create_dataset()
    save_dataset(toc_df, 'toc')

    # fig_df = fig_classification.create_dataset()
    # save_dataset(fig_df, 'fig')

    heading_id_toc_df = heading_id_toc.create_dataset()
    save_dataset(heading_id_toc_df, 'heading_id_toc')

    marginals_df = marginals_classification.create_dataset()
    save_dataset(marginals_df, 'marginal_lines')


def create_training_sets_pt2():
    proc_df = heading_id_toc.pre_process_id_dataset(datafile=paths.get_dataset_path('heading_id_toc'))
    save_dataset(proc_df, 'processed_heading_id_toc')

    # page_id_df = page_identification.create_dataset()
    # save_dataset(page_id_df, 'page_id')

    heading_id_intext_df = heading_id_intext.create_dataset()
    save_dataset(heading_id_intext_df, 'heading_id_intext')


# def create_training_sets_pt3():
#     page_ex_df = page_extraction.create_dataset()
#     save_dataset(page_ex_df, 'page_extraction')
#
#     heading_class_df = heading_classification.create_dataset()
#     save_dataset(heading_class_df, 'heading_classification')


def train_models_pt1():  # run model training. output report of how they all did
    toc_classification.train()
    # fig_classification.train()
    marginals_classification.train()


def train_models_pt2():
    heading_id_toc_nn = heading_id_toc.NeuralNetwork()
    heading_id_toc_nn.train()

    # page_id_nn = page_identification.NeuralNetwork()
    # page_id_nn.train()

    heading_id_intext.train()
    heading_id_intext.train(model_file=paths.get_model_path('heading_id_intext_no_toc'))


# def train_models_pt3():
#     page_ex_nn = page_extraction.NeuralNetwork()
#     page_ex_nn.train()
#
#     heading_classification.train()  # commenting this out now as I don't use it


def accuracy_dif(scores):
    if len(scores) < 3:
        return False
    scores.append(0)
    c1 = [x for x in scores].insert(0, 0)  # inserts 0 value at front to push list one index along
    score_diffs = c1 - scores
    score_diffs.pop(0), score_diffs.pop(-1)  # pop front and end as they don't contain proper values
    print(score_diffs)
    plt.plot(score_diffs)
    return False  # just see how it's going, return True once the difference between the scores gets negligible


def test():
    ds = time.time()
    toc_df = toc_classification.create_dataset()
    de = time.time()
    print("time to create dataset: ", de - ds)
    save_dataset(toc_df, 'toc')
    ss = time.time()
    print ("time to save dataset: ", ss - de)
    accuracies = []

    while not accuracy_dif(accuracies):
        time.sleep(15)
        toc_classification.train()
        active_learning.automatically_tag('toc', toc_classification.classify_page, 'TOCPage')
        toc_classification.check_tags()
        toc_classification.train(n_queries=5)
        active_learning.automatically_tag('toc', toc_classification.classify_page, 'TOCPage')
        toc_classification.tag_prevpagetoc()
        toc_classification.train(n_queries=5)
        accuracy = toc_classification.train(n_queries=0)  # evaluate mode
        accuracies.append(accuracy)


if __name__ == "__main__":
    test()
    # bad_dir = "training/restructpageinfo/bad_criteria/"
    # settings.dataset_version = 'expansion1'
    # # add preliminary step that textracts and clean_and_restructs files
    # # training files will be all in training/restructpageinfo folder, so should filter the members of that first
    # restructpageinfo_path = (glob.glob('training/restructpageinfo/*.json'))
    # reportids = [x.split('\\')[-1].replace('_1_restructpageinfo.json', '') for x in restructpageinfo_path]
    # for report in restructpageinfo_path:
    #     bad_criteria = check_report_criteria()
    #     if bad_criteria:
    #         print("Report: ", report, "does not fit report criteria: ", bad_criteria)
    #         if not os.environ.path(bad_dir):
    #             os.mkdir(bad_dir)
    #         bad_path = bad_dir + (restructpageinfo_path.split("/"))[0]
    #         os.rename(restructpageinfo_path, bad_path)  # move file from main restruct folder to a subfolder
    #
    # create_training_sets_pt1()

    # manually annotate training sets before each train
    #break

    #train_models_pt1()
    #create_training_sets_pt2()

    # break

    #train_models_pt2()
    #create_training_sets_pt3()

    # break

    #train_models_pt3()

