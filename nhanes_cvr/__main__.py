if __name__ == '__main__':
    import nhanes_cvr.app as app
    app.runHandPickedFeatures()
    app.runCorrelationFeatureSelection()
    app.runCorrelationFeatureSelectionDropNulls()
