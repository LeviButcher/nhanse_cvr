import matplotlib
import matplotlib.pyplot as plt
import nhanes_cvr.combinefeatures as cf
from sklearn import ensemble, model_selection, neighbors, neural_network, preprocessing, svm, linear_model
from nhanes_cvr.BalancedKFold import BalancedKFold, RepeatedBalancedKFold
from sklearn.metrics import accuracy_score, f1_score, make_scorer, precision_score, recall_score
from nhanes_dl import download, types
import nhanes_cvr.gridsearch as gs
import nhanes_cvr.utils as utils
import seaborn as sns


# CONFIGURATION VARIABLES
scores = {"precision": make_scorer(precision_score, average="binary", zero_division=0),
          "recall": make_scorer(recall_score, average="binary", zero_division=0),
          "f1": make_scorer(f1_score, average="binary", zero_division=0),
          "accuracy": make_scorer(accuracy_score)}
targetScore = "precision"
maxIter = 500
randomState = 42
folds = 10
foldRepeats = 10

foldingStrategies = [
    model_selection.KFold(n_splits=folds, shuffle=True,
                          random_state=randomState),
    model_selection.StratifiedKFold(
        n_splits=folds, shuffle=True, random_state=randomState),
    BalancedKFold(n_splits=folds, shuffle=True, random_state=randomState),
    # RepeatedBalancedKFold(n_splits=folds)
]


# Store Model in Thunks to ensure recreation of new model every GridSearch
models = [
    (lambda: linear_model.LogisticRegression(random_state=randomState, max_iter=maxIter),
     [
        {
            "C": [.5, 1],
            "penalty": ["l2"],
            "solver": ["newton-cg", "lbfgs", "liblinear", "sag", "saga"]
        },
        {
            "C": [.5, 1],
            "penalty": ["l1"],
            "solver": ["liblinear", "saga"]
        }
    ]),

    (lambda: linear_model.SGDClassifier(shuffle=True, random_state=randomState),
        {"loss": ["perceptron", "log", "perceptron"], "penalty":["l1", "l2"]}),

    (lambda: linear_model.RidgeClassifier(random_state=randomState), [
        {"solver": [
            "sag", "svd", "lsqr", "cholesky", "sparse_cg", "sag", "saga"]},
        {"solver": ["lbfgs"], "positive": [True]}
    ]),

    (lambda: ensemble.RandomForestClassifier(random_state=randomState), {
     "class_weight": [None, "balanced", "balanced_subsample"]}
     ),

    (lambda: neighbors.KNeighborsClassifier(),
     {"weights": ["uniform", "distance"]}),

    (lambda: neural_network.MLPClassifier(shuffle=True, max_iter=maxIter), {
     "activation": ["logistic", "tanh", "relu"],
     "solver": ["lbfgs", "sgd", "adam"],
     "learning_rate":["invscaling"]
     }),

    (lambda: svm.LinearSVC(random_state=42), [
        {
            "loss": ["hinge"],
            "penalty": ['l2'],
            "C": [.05, 1],
        }, {
            "loss": ["squared_hinge"],
            "penalty": ['l2'],
            "C": [.05, 1],
        }
    ])
]


scalers = [
    None,
    preprocessing.MinMaxScaler(),
    preprocessing.Normalizer(),
    preprocessing.StandardScaler(),
    preprocessing.RobustScaler()
]

downloadConfig = {
    download.CodebookDownload(types.ContinuousNHANES.First,
                              "LAB13", "LAB13AM", "LAB10AM", "LAB18", "CDQ",
                              "DIQ", "BPQ", "BMX", "DEMO", "BPX"),
    download.CodebookDownload(types.ContinuousNHANES.Second,
                              "L13_B", "L13AM_B", "L10AM_B", "L10_2_B",
                              "CDQ_B", "DIQ_B", "BPQ_B", "BMX_B", "DEMO_B", "BPX_B"),
    download.CodebookDownload(types.ContinuousNHANES.Third,
                              "L13_C", "L13AM_C", "L10AM_C", "CDQ_C", "DIQ_C",
                              "BPQ_C", "BMX_C", "DEMO_C", "BPX_C"),
    # Everything past this point has the same feature (Mostly)
    download.CodebookDownload(types.ContinuousNHANES.Fourth,
                              "TCHOL_D", "TRIGLY_D", "HDL_D", "GLU_D", "CDQ_D",
                              "DIQ_D", "BPQ_D", "BMX_D", "DEMO_D", "BPX_D"),
    download.CodebookDownload(types.ContinuousNHANES.Fifth,
                              "TCHOL_E", "TRIGLY_E", "HDL_E", "GLU_E", "CDQ_E",
                              "DIQ_E", "BPQ_E", "BMX_E", "DEMO_E", "BPX_E"),
    download.CodebookDownload(types.ContinuousNHANES.Sixth,
                              "TCHOL_F", "TRIGLY_F", "HDL_F", "GLU_F", "CDQ_F",
                              "DIQ_F", "BPQ_F", "BMX_F", "DEMO_F", "BPX_F"),
    download.CodebookDownload(types.ContinuousNHANES.Seventh,
                              "TCHOL_G", "TRIGLY_G", "HDL_G", "GLU_G", "CDQ_G",
                              "DIQ_G", "BPQ_G", "BMX_G", "DEMO_G", "BPX_G"),
    download.CodebookDownload(types.ContinuousNHANES.Eighth,
                              "TCHOL_H", "TRIGLY_H", "HDL_H", "GLU_H", "CDQ_H",
                              "DIQ_H", "BPQ_H", "BMX_H", "DEMO_H", "BPX_H"),
}


# Gotta check to make sure "no" is 2
def replaceMissingWithNo(X):
    return cf.replaceMissingWith(2, X)


def standardYesNoProcessor(X):
    return X.apply(lambda x: 1 if x == 1 else 0)


# # NOTE: NHANSE dataset early on had different variables names for some features
# # CombineFeatures is used to combine these features into a single feature
combineConfigs = [
    # --- Lab Work ---
    cf.rename("LBXTC", "Total_Chol", postProcess=cf.meanMissingReplacement),
    cf.rename("LBDLDL", "LDL", postProcess=cf.meanMissingReplacement),
    cf.create(["LBDHDL", "LBXHDD", "LBDHDD"], "HDL",
              postProcess=cf.meanMissingReplacement),
    cf.create(["LBXSGL", "LB2GLU", "LBXGLU"], "FBG",
              postProcess=cf.meanMissingReplacement),
    # triglercyides
    cf.rename("LBXTR", "TG", postProcess=cf.meanMissingReplacement),
    # --- Questionaire ---
    cf.rename("DIQ010", "DIABETES", postProcess=standardYesNoProcessor),
    cf.rename("DIQ170", "TOLD_AT_RISK_OF_DIABETES",
              postProcess=standardYesNoProcessor),
    cf.rename("DIQ200A", "CONTROLLING_WEIGHT",
              postProcess=standardYesNoProcessor),
    cf.rename(
        "BPQ020", "HIGH_BLOOD_PRESSURE", postProcess=standardYesNoProcessor),
    cf.rename("BPQ030", "HIGH_BLOOD_PRESSURE_TWO_OR_MORE",
              postProcess=standardYesNoProcessor),
    cf.rename("BPQ050A", "TAKEN_DRUGS_FOR_HYPERTEN",
              postProcess=standardYesNoProcessor),
    cf.rename(
        "CDQ001", "CHEST_PAIN", postProcess=standardYesNoProcessor),
    # cf.rename("DBQ700", "HEALTHY_DIET") # Not in 1999
    # --- Measurements ---
    cf.rename("BMXBMI", "BMI", postProcess=cf.meanMissingReplacement),
    cf.rename("BMXWAIST", "WC", postProcess=cf.meanMissingReplacement),
    cf.create(["BPXSY1", "BPXSY2", "BPXSY3", "BPXSY4"], "SYSTOLIC",
              combineStrategy=cf.meanCombine, postProcess=cf.meanMissingReplacement),
    cf.create(["BPXDI1", "BPXDI2", "BPXDI3", "BPXDI4"], "DIASTOLIC",
              combineStrategy=cf.meanCombine, postProcess=cf.meanMissingReplacement),
    cf.rename("RIAGENDR", "GENDER"),
    cf.rename("RIDAGEYR", "AGE"),
]

# Download NHANES
NHANES_DATASET = utils.cache_nhanes("./data/nhanes.csv",
                                    lambda: download.downloadCodebooksWithMortalityForYears(downloadConfig))

# Process NHANES
LINKED_DATASET = NHANES_DATASET.loc[NHANES_DATASET.ELIGSTAT == 1, :]
DEAD_DATASET = LINKED_DATASET.loc[LINKED_DATASET.MORTSTAT == 1, :]
# withoutScalingFeatures = ["DIABETES", "HYPERTEN", "GENDER"]
withoutScalingFeatures = [
    c.combinedName for c in combineConfigs if c.postProcess.__name__ == standardYesNoProcessor.__name__]


print(f"Not Scaling: {withoutScalingFeatures}")

print(f"Entire Dataset: {NHANES_DATASET.shape}")
print(f"Linked Mortality Dataset: {LINKED_DATASET.shape}")
print(f"Dead Dataset: {DEAD_DATASET.shape}")

DEAD_DATASET.describe().to_csv("./results/dead_dataset_info.csv")

dataset = DEAD_DATASET  # Quickly allows running on other datasets

ccDF = cf.combineFeaturesToDataFrame(combineConfigs)
ccDF.to_csv("./results/combineFeatures.csv")

Y = utils.labelCauseOfDeathAsCVR(dataset)
X = cf.runCombines(combineConfigs, dataset)

# Setup Configs
scalingConfigs = gs.createScalerConfigsIgnoreFeatures(
    scalers, X, withoutScalingFeatures)

gridSearchConfigs = gs.createGridSearchConfigs(
    models, scalingConfigs, foldingStrategies, [scores])

# Run Training
res = gs.runMultipleGridSearchAsync(gridSearchConfigs, targetScore, X, Y)

# Evaluate Results
resultsDF = gs.resultsToDataFrame(res)
gs.plotResults3d(resultsDF, targetScore)
resultsDF.to_csv("./results/results.csv")

print("\n--- FINISHED ---\n")
print(f"Ran {len(gridSearchConfigs)} Configs")
gs.printBestResult(res)


# Start of correlation feature selection
# TODO Follow article: https://towardsdatascience.com/feature-selection-with-pandas-e3690ad8504b
plt.figure(figsize=(12, 10))
cor = DEAD_DATASET.corr()
# sns.heatmap(cor, annot=True, cmap=plt.cm.Reds)
cor_target = abs(cor["MEDV"])
relevant_features = cor_target[cor_target > 0.5]
print(relevant_features)
# plt.show()