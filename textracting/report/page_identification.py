## @file
# Page number identification module: Functions for identifying if a marginal contains a page number
# by Anna Andraszek

import pandas as pd
import paths
import re
import string
from report import active_learning, machine_learning_helper as mlh
from keras.wrappers.scikit_learn import KerasClassifier
import tensorflow as tf
import pickle
import os
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Embedding
from sklearn.pipeline import Pipeline
from report.heading_id_toc import Text2Seq
from sklearn.preprocessing import FunctionTransformer

os.environ['KMP_WARNINGS'] = '0'
months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
          'november', 'december']
## model name
name = 'page_id'
## name of column containing y values
y_column = 'tag'
## column names to exclude from training
limit_cols = ['transformed']
## column names to include in training
include_cols = ['original']
## column names in dataset
columns = ['original', 'transformed', y_column]

class NeuralNetwork():
    epochs = 15
    batch_size = 15
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    #model_path = settings.model_path

    def __init__(self):
        #self.model_name = 'page_id_' + model_name
        #self.model_loc = settings.get_model_path('page_id') #self.model_path + self.model_name + '.h5'
        #self.tok_loc = settings.get_model_path('page_id', tokeniser=True)  #self.model_path + self.model_name + 'tokeniser.joblib'
        print()

    def train(self, n_queries=10, mode=paths.dataset_version):  #settings.marginals_id_trans_dataset):
        file = paths.get_dataset_path(name, mode)
        df = pd.read_csv(file)
        #self.X = df['transformed']
        #self.Y = df['tag']
        self.max_words, self.max_len = check_maxlens(df)

        lstm = KerasClassifier(build_fn=self.LSTM, batch_size=self.batch_size, epochs=self.epochs,
                               validation_split=0.2)

        estimator = Pipeline([
            #('transform1', ColumnTransformer([
                ('transform_text', FunctionTransformer(transform_text_wrapper)),# 0)
                #], remainder="passthrough")),
            ('transform2', Text2Seq(classes=2)),
            ('lstm', lstm)
        ], verbose=True)

        accuracy, learner = active_learning.train(df, y_column, n_queries, estimator, file, limit_cols=limit_cols)
        self.model = learner
        # self.tok = Tokenizer(num_words=self.max_words+1) # only num_words-1 will be taken into account!
        # self.model = self.LSTM()
        #
        # X_train, X_test, Y_train, Y_test = train_test_split(self.X, self.Y, test_size=0.15)
        #
        # self.tok.fit_on_texts(X_train)
        # sequences = self.tok.texts_to_sequences(X_train)
        # sequences_matrix = sequence.pad_sequences(sequences, maxlen=self.max_len)
        # y_binary = to_categorical(Y_train)
        # self.model.summary()
        # self.model.fit(sequences_matrix, y_binary, batch_size=self.batch_size, epochs=self.epochs,
        #           validation_split=0.2) #, callbacks=[EarlyStopping(monitor='val_loss',min_delta=0.0001)]
        #
        # test_sequences = self.tok.texts_to_sequences(X_test)
        # test_sequences_matrix = sequence.pad_sequences(test_sequences, maxlen=self.max_len)
        #
        # accr = self.model.evaluate(test_sequences_matrix, to_categorical(Y_test))
        # print('Test set\n  Loss: {:0.3f}\n  Accuracy: {:0.3f}'.format(accr[0], accr[1]))
        self.model_loc = paths.get_model_path(name, mode)
        #self.model.save(self.model_loc)
        #joblib.dump(self.tok, self.tok_loc)
        with open(self.model_loc, "wb") as f:
            pickle.dump(self.model, f)


    def LSTM(self):
        model = Sequential()
        model.add(Embedding(self.max_words+1, output_dim=self.max_len))#256))
        model.add(LSTM(128))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))

        model.compile(loss='binary_crossentropy',
                      optimizer='rmsprop',
                      metrics=['accuracy'])
        return model


    def load_model_from_file(self, model_loc):
        if model_loc is None:
            model_loc = self.model_loc
        self.model = pickle.load(model_loc)
        #self.tok = joblib.load(self.tok_loc)
        self.model._make_predict_function()


    def predict(self, strings, mode=paths.dataset_version):
        # if not os.path.exists(self.model_loc):
        #     self.train()
        # try:
        #     self.model
        # except AttributeError:
        #     self.load_model_from_file()
        #strings = strings.apply(lambda x: transform_text(x))
        # sequences = self.tok.texts_to_sequences(strings)
        # sequences_matrix = sequence.pad_sequences(sequences, maxlen=12)
        # predictions = self.model.predict(sequences_matrix)
        # return predictions, np.argmax(predictions, axis=1)
        return mlh.get_classified(strings, name, y_column, limit_cols, mode, masked=False)

def check_maxlens(df):
    series = df['transformed']
    seqs = series.str.lower().str.split()
    max_seq_len = len(max(seqs, key=lambda x:len(x)))
    all_words = []
    seqs.apply(lambda x: all_words.extend(x))
    unique_words = len(set(all_words))
    #max_words = len(words.unique())
    return unique_words, max_seq_len


def transform_text_wrapper(series, transform_all=True):
    if isinstance(series, pd.DataFrame):
        if len(series.columns) == 1:
            series = pd.Series(data=series.iloc[:,0])
        else:
            raise KeyError('Pass a DataFrame with a single column, or a Series')
    return series.apply(lambda x: transform_text(x, transform_all))


def transform_text(text, transform_all=True):
    text = text.translate(text.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    tokens = text.split(r' ')
    new_text = ''
    for token in tokens:
        token = token.lower()
        if re.match(r'^\t', token):  # tab character
            new_text += 'tab '
            token = token.strip('\t')
        if re.match(r'^[0-9][0-9]?$', token):  # one or two digit number
            if transform_all:
                new_text += 'smallNum '
            else:
                new_text += token + ' '
        elif re.match(r'^[0-9][0-9][0-9]$', token):  # three digit number
            new_text += 'mediumNum '
        elif re.match(r'^[0-9]+$', token):  # any digit number (at this point, higher than three digit)
            new_text += 'bigNum '
        elif token.lower() in months:  # name of a month
            new_text += 'month '
        elif re.match(r'^page$', token):  # 'page'
            new_text += 'page '
        elif re.match(r'^appendix$', token):  # 'appendix'
            new_text += 'appendix '
        elif re.match(r'^[a-z]+$', token):  # any letter-only word
            new_text += 'word '
        elif not re.match(r'^(|\s+)$', token):  # any string which is not empty or only whitespace
            new_text += 'mix '
    return new_text


def create_dataset():
    sourcefile = paths.get_dataset_path('marginal_lines')
    texts = pd.read_csv(sourcefile, usecols=['Text', 'Marginal'])
    texts = texts.loc[texts['Marginal'] > 0]
    new_texts = pd.DataFrame(columns=columns)
    new_texts['original'] = texts['Text']
    new_texts['transformed'] = texts.Text.apply(lambda x: transform_text(x))
    new_texts['tag'] = None
    #print(new_text)
    #new_text.to_csv(settings.marginals_id_trans_dataset, index=False)
    return new_texts


def run_model(mode=paths.production):
    nn = NeuralNetwork()
    model_loc = paths.get_model_path(name, mode=mode)
    nn.load_model_from_file(model_loc=model_loc)
    df = pd.read_csv(paths.get_dataset_path(name, mode=mode), usecols=['original'])
    #df = pd.read_csv(paths.marginals_id_trans_dataset, usecols=['original'])
    #data = df.original
    data = pd.Series(['page 8', 'bhp hello 3', '12 month report', 'epm3424 3 february 1900',
                                 'epm23 february 2000', 'epm34985 4000'])
    p, r = nn.predict(data)#.original)

    for i, row in df.iterrows():
        print(row.original, ', ', p[i], ', ', r[i])


def train(n_queries=10, mode=paths.dataset_version):
    if not os.path.exists(paths.get_dataset_path('page_id', mode)):
        df = create_dataset()
        df.to_csv(paths.get_dataset_path('page_id', mode), index=False)
    nn = NeuralNetwork()
    nn.train(n_queries=n_queries, mode=mode)


def get_page_marginals(marginals, mode=paths.dataset_version):
    if len(marginals) > 0:
        nn = NeuralNetwork()
        p, r = nn.predict(marginals, mode)#.original)
        return r
    else:
        return []


if __name__ == "__main__":
    train()
    #create_dataset()
    #nn = NeuralNetwork()
    #nn.train()
    #run_model()

    # result
    # [[1.93149030e-01 8.52303803e-01]
    #  [1.55359507e-04 9.99890804e-01]
    #  [7.03883052e-01 3.61839056e-01]
    #  [9.63378191e-01 3.04489434e-02]
    #  [8.78076196e-01 1.08638585e-01]
    #  [9.87653494e-01 1.31420493e-02]
    #  [9.74116623e-01 2.65470557e-02]]
    # ------------------
    # [1 1 0 0 0 0 0]