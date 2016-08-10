# TODO pass in user somehow
# TODO show error notification for failures
@app.route("/task_complete", methods=['POST'])
def task_complete():
    data = request.get_json()
    if 'fset_id' in data:
        fset = m.Featureset.get(m.Featureset.id == data['fset_id'])
        if data['status'] == 'success':
            fset.task_id = None
            fset.finished = datetime.datetime.now()
            fset.save()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Featureset '{}'" " finished.".format(fset.name)})
            return success({"id": fset.id}, 'cesium/FETCH_FEATURESETS')
        elif data['status'] == 'error':
            fset.delete_instance()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Featureset '{}'" " failed. Please try"
                             " again".format(fset.name), "type": "error"})
            return success({"id": fset.id}, 'cesium/FETCH_FEATURESETS')
    elif 'model_id' in data:
        model = m.Model.get(m.Model.id == data['model_id'])
        if data['status'] == 'success':
            model.task_id = None
            model.finished = datetime.datetime.now()
            model.save()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Model '{}'" " finished.".format(model.name)})
            return success({"id": model.id}, 'cesium/FETCH_MODELS')
        elif data['status'] == 'error':
            model.delete_instance()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Model '{}' failed."
                             " Please try again.".format(model.name),
                             "type": "error"})
            return success({"id": model.id}, 'cesium/FETCH_MODELS')
    elif 'prediction_id' in data:
        prediction = m.Prediction.get(m.Prediction.id == data['prediction_id'])
        if data['status'] == 'success':
            prediction.task_id = None
            prediction.finished = datetime.datetime.now()
            prediction.save()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Prediction '{}'/'{}'"
                             " finished.".format(prediction.dataset.name,
                                                prediction.model.name)})
            return success({"id": prediction.id}, 'cesium/FETCH_PREDICTIONS')
        elif data['status'] == 'error':
            prediction.delete_instance()
            success(action='cesium/SHOW_NOTIFICATION',
                    payload={"note": "Prediction '{}'/'{}'" " failed. Please try"
                             " again.".format(prediction.dataset.name,
                                            prediction.model.name),
                             "type": "error" })
            return success({"id": prediction.id}, 'cesium/FETCH_PREDICTIONS')
    else:
        raise ValueError('Unrecognized task type')
