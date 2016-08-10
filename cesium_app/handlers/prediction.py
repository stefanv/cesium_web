@app.route('/predictions', methods=['POST', 'GET'])
@app.route('/predictions/<prediction_id>', methods=['GET', 'PUT', 'DELETE'])
@exception_as_error
def predictions(prediction_id=None):
    """
    """
    # TODO: ADD MORE ROBUST EXCEPTION HANDLING (HERE AND ALL OTHER FUNCTIONS)
    if request.method == 'POST':
        data = request.get_json()

        dataset_id = data['datasetID']
        model_id = data['modelID']

        dataset = m.Dataset.get(m.Dataset.id == data["datasetID"])
        model = m.Model.get(m.Model.id == data["modelID"])
        if model.finished is None:
            raise RuntimeError("Can't predict for in-progress model.")
        fset = model.featureset
        if fset.finished is None:
            raise RuntimeError("Can't predict for in-progress featureset.")
        prediction_path = pjoin(cfg['paths']['predictions_folder'],
                                '{}_prediction.nc'.format(uuid.uuid4()))
        prediction_file = m.File.create(uri=prediction_path)
        prediction = m.Prediction.create(file=prediction_file, dataset=dataset,
                                         project=dataset.project, model=model)
        res = predict_and_notify(get_username(), prediction.id, dataset.uris,
            fset.features_list, model.file.uri, prediction_path,
            custom_features_script=fset.custom_features_script).apply_async()

        prediction.task_id = res.task_id
        prediction.save()

        return success(prediction, 'cesium/FETCH_PREDICTIONS')

    elif request.method == 'GET':
        if prediction_id is not None:
            prediction = m.Prediction.get(m.Prediction.id == prediction_id)
            prediction_info = prediction.display_info()
        else:
            predictions = [prediction for p in m.Project.all(get_username())
                           for prediction in p.predictions]
            prediction_info = [p.display_info() for p in predictions]
        return success(prediction_info)

    elif request.method == 'DELETE':
        if prediction_id is None:
            return error("Invalid request - prediction set ID not provided.")

        f = m.Prediction.get(m.Prediction.id == prediction_id)
        if f.is_owned_by(get_username()):
            f.delete_instance()
        else:
            raise UnauthorizedAccess("User not authorized for project.")

        return success(action='cesium/FETCH_PREDICTIONS')

    elif request.method == 'PUT':
        if prediction_id is None:
            return error("Invalid request - prediction set ID not provided.")

        return error("Functionality for this endpoint is not yet implemented.")
