@app.route('/models', methods=['POST', 'GET'])
@app.route('/models/<model_id>', methods=['GET', 'PUT', 'DELETE'])
@exception_as_error
def Models(model_id=None):
    """
    """
    # TODO: ADD MORE ROBUST EXCEPTION HANDLING (HERE AND ALL OTHER FUNCTIONS)
    if request.method == 'POST':
        data = request.get_json()

        model_name = data.pop('modelName')
        featureset_id = data.pop('featureSet')
        # TODO remove cast once this is passed properly from the front end
        model_type = sklearn_model_descriptions[int(data.pop('modelType'))]['name']
        project_id = data.pop('project')

        fset = m.Featureset.get(m.Featureset.id == featureset_id)
        if fset.finished is None:
            raise RuntimeError("Can't build model for in-progress featureset.")

        model_params = data

        model_params = {k: util.robust_literal_eval(v)
                        for k, v in model_params.items()}

        # TODO split out constant params / params to optimize
        model_params, params_to_optimize = model_params, {}
        util.check_model_param_types(model_type, model_params)

        model_path = pjoin(cfg['paths']['models_folder'],
                           '{}_model.nc'.format(uuid.uuid4()))

        model_file = m.File.create(uri=model_path)
        model = m.Model.create(name=model_name, file=model_file,
                               featureset=fset, project=fset.project,
                               params=model_params, type=model_type)

        res = build_model_and_notify(get_username(), model.id, model_type,
                                     model_params, fset.file.uri,
                                     model_file.uri,
                                     params_to_optimize).apply_async()
        model.task_id = res.task_id
        model.save()

        return success(data={'message': "We're working on your model"},
                       action='cesium/FETCH_MODELS')

    elif request.method == 'GET':
        if model_id is not None:
            model_info = m.Model.get(m.Model.id == model_id)
        else:
            model_info = [model for p in m.Project.all(get_username())
                          for model in p.models]
        return success(model_info)

    elif request.method == 'DELETE':
        if model_id is None:
            return error("Invalid request - model set ID not provided.")

        f = m.Model.get(m.Model.id == model_id)
        if f.is_owned_by(get_username()):
            f.delete_instance()
        else:
            raise UnauthorizedAccess("User not authorized for project.")

        return success(action='cesium/FETCH_MODELS')

    elif request.method == 'PUT':
        if model_id is None:
            return error("Invalid request - model set ID not provided.")

        return error("Functionality for this endpoint is not yet implemented.")
