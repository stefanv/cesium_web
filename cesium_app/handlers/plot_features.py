@app.route('/plot_features/<featureset_id>', methods=['GET'])
@exception_as_error
def PlotFeatures(featureset_id):
    fset = m.Featureset.get(m.Featureset.id == featureset_id)
    if not fset.is_owned_by(get_username()):
        raise RuntimeError("User not authorized")
    features_to_plot = sorted(fset.features_list)[0:4]
    data, layout = plot.feature_scatterplot(fset.file.uri, features_to_plot)
    return success({'data': data, 'layout': layout})
