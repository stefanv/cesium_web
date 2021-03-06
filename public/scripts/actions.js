// Action format:
// https://github.com/acdlite/flux-standard-action

import {reset as resetForm} from 'redux-form';

export const HYDRATE = 'cesium/HYDRATE'

export const FETCH_PROJECTS = 'cesium/FETCH_PROJECTS'
export const RECEIVE_PROJECTS = 'cesium/RECEIVE_PROJECTS'
export const ADD_PROJECT = 'cesium/ADD_PROJECT'
export const DELETE_PROJECT = 'cesium/DELETE_PROJECT'
export const SELECT_PROJECT = 'cesium/SELECT_PROJECT'
export const UPDATE_PROJECT = 'cesium/UPDATE_PROJECT'
export const HIDE_NEWPROJECT_FORM = 'cesium/HIDE_NEWPROJECT_FORM'

export const FETCH_DATASETS = 'cesium/FETCH_DATASETS'
export const RECEIVE_DATASETS = 'cesium/RECEIVE_DATASETS'
export const UPLOAD_DATASET = 'cesium/UPLOAD_DATASET'

export const FETCH_FEATURES = 'cesium/FETCH_FEATURES'
export const FETCH_FEATURESETS = 'cesium/FETCH_FEATURESETS'
export const RECEIVE_FEATURES = 'cesium/RECEIVE_FEATURES'
export const RECEIVE_FEATURESETS = 'cesium/RECEIVE_FEATURESETS'
export const COMPUTE_FEATURES = 'cesium/COMPUTE_FEATURES'
export const DELETE_FEATURESET = 'cesium/DELETE_FEATURESET'

export const FETCH_MODELS = 'cesium/FETCH_MODELS'
export const RECEIVE_MODELS = 'cesium/RECEIVE_MODELS'
export const CREATE_MODEL = 'cesium/CREATE_MODEL'

export const FETCH_PREDICTIONS = 'cesium/FETCH_PREDICTIONS'
export const RECEIVE_PREDICTIONS = 'cesium/RECEIVE_PREDICTIONS'
export const DO_PREDICTION = 'cesium/DO_PREDICTION'

export const SHOW_NOTIFICATION = 'cesium/SHOW_NOTIFICATION'
export const HIDE_NOTIFICATION = 'cesium/HIDE_NOTIFICATION'

export const TOGGLE_EXPANDER = 'cesium/TOGGLE_EXPANDER'
export const HIDE_EXPANDER = 'cesium/HIDE_EXPANDER'
export const SHOW_EXPANDER = 'cesium/SHOW_EXPANDER'

export const FETCH_SKLEARN_MODELS = 'cesium/FETCH_SKLEARN_MODELS'
export const RECEIVE_SKLEARN_MODELS = 'cesium/RECEIVE_SKLEARN_MODELS'


// Refactor this into a utility function
String.prototype.format = function () {
  var i = 0, args = arguments;
  return this.replace(/{}/g, function () {
    return typeof args[i] != 'undefined' ? args[i++] : '';
  });
};


export function hydrate() {
  return dispatch => {
    dispatch(fetchProjects())
      .then(proj => {
        dispatch(fetchDatasets());
        dispatch(fetchFeaturesets());
        dispatch(fetchFeatures());
        dispatch(fetchModels());
      })
    dispatch(fetchSklearnModels());
  }
}

function promiseAction(dispatch, action_type, promise) {
  dispatch({
    type: action_type,
    payload: {
      promise: promise
    }
  });
  return promise;
}


// Download projects
export function fetchProjects() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_PROJECTS,

      fetch('/project')
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(receiveProjects(json.data))
          } else {
            dispatch(
              showNotification(
                'Error downloading projects ({})'.format(json.message)
              ));
          }
          return json;
        }
        ).catch(ex => console.log('fetchProjects exception:', ex))
      )
}

// Add a new project
export function addProject(form) {
  return dispatch =>
    promiseAction(
      dispatch,
      ADD_PROJECT,

      fetch('/project',
            {method: 'POST',
             body: JSON.stringify(form),
             headers: new Headers({
               'Content-Type': 'application/json'
             })})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(resetForm('newProject'));
            dispatch(showNotification('Successfully added new project'))
            dispatch(selectProject(json.data.id));
          } else {
            return Promise.reject({_error: json.message});
          }
          return json;
        })
  )
}


// Update an existing project
export function updateProject(form) {
  return dispatch =>
    promiseAction(
      dispatch,
      UPDATE_PROJECT,

      fetch('/project/{}'.format(form.projectId),
            {method: 'PUT',
             body: JSON.stringify(form),
             headers: new Headers({
               'Content-Type': 'application/json'
             })})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(resetForm('newProject'));
            dispatch(showNotification('Successfully updated project'))
          } else {
            return Promise.reject({_error: json.message});
          }
          return json;
        })
  )
}


export function deleteProject(id) {
  return dispatch =>
    promiseAction(
      dispatch,
      DELETE_PROJECT,

      fetch('/project/' + id, {method: 'DELETE'})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(showNotification('Project successfully deleted'));
            dispatch(selectProject());
          } else {
            dispatch(
              showNotification(
                'Error deleting project ({})'.format(json.message)
              ));
          }
        })
  )
}



// Receive list of projects
function receiveProjects(projects) {
  return {
    type: RECEIVE_PROJECTS,
    payload: projects
  }
}

let objectType = (obj) => (
  Object.prototype.toString.call(obj).slice(8, -1)
)

export function uploadDataset(form) {
  let formData = new FormData();

  for (let key in form) {
    if (objectType(form[key][0]) === 'File') {
      formData.append(key, form[key][0])
    } else {
      formData.append(key, form[key])
    }
  }

  return dispatch =>
    promiseAction(
      dispatch,
      UPLOAD_DATASET,

      fetch('/dataset', {method: 'POST', body: formData})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(showNotification('Successfully uploaded new dataset'))
            dispatch(hideExpander('newDatasetExpander'));
            dispatch(resetForm('newDataset'));
          } else {
            return Promise.reject({_error: json.message});
          }
          return json;
        })
  )
}

// Download datasets
export function fetchDatasets() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_DATASETS,

      fetch('/dataset')
        .then(response => response.json())
        .then(json => {
          return dispatch(receiveDatasets(json.data))
        }
        ).catch(ex => console.log('fetchDatasets', ex))
    )
}

// Receive list of projects
function receiveDatasets(datasets) {
  return {
    type: RECEIVE_DATASETS,
    payload: datasets
  }
}


// Download featuresets
export function fetchFeaturesets() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_FEATURESETS,

      fetch('/features')
        .then(response => response.json())
        .then(json => {
          return dispatch(receiveFeaturesets(json.data))
        }
        ).catch(ex => console.log('fetchFeaturesets', ex))
  )
}

// Receive list of featuresets
function receiveFeaturesets(featuresets) {
  return {
    type: RECEIVE_FEATURESETS,
    payload: featuresets
  }
}


// POST new featureset form
export function submitNewFeatureset(formdata) {
  return dispatch => (
    fetch('/features',
          {
            method: 'POST',
            headers: new Headers({
              'Content-Type': 'application/json'
            }),
            body: JSON.stringify(formdata)
          }
    ).then(response => response.json())
     .then(json => {
       console.log('Added new feature set');
       return json;
     }
     ).catch(ex => console.log('submitNewFeatureset', ex))
  )
}

// Clear features form after submit
function clearFeaturesForm() {
  return {
    type: CLEAR_FEATURES_FORM
  }
}


export function createModel(form) {
  return dispatch =>
    promiseAction(
      dispatch,
      CREATE_MODEL,

      fetch('/models',
            {method: 'POST',
             body: JSON.stringify(form),
             headers: new Headers({
               'Content-Type': 'application/json'
             })})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(resetForm('newModel'));
            dispatch(hideExpander('newModelExpander'));
            dispatch(showNotification('Successfully added new model'));
          } else {
            return Promise.reject({_error: json.message});
          }
          return json;
        })
  )
}

export function showNotification(text) {
  return (dispatch) => {
    setTimeout(() => dispatch(hideNotification()), 3500);
    dispatch({
      type: SHOW_NOTIFICATION,
      payload: text
    });
  }
}

export function hideNotification() {
  return {
    type: HIDE_NOTIFICATION
  }
}

export function hideExpander(id) {
  return {
    type: HIDE_EXPANDER,
    payload: {
      id: id
    }
  }
}

export function showExpander(id) {
  return {
    type: SHOW_EXPANDER,
    payload: {
      id: id
    }
  }
}

export function toggleExpander(id) {
  return {
    type: TOGGLE_EXPANDER,
    payload: {
      id: id
    }
  }
}

// Currently, used upon creation of a new project to switch to that project
export function selectProject(id=null) {
  return dispatch => {
    dispatch(hideExpander('newProjectExpander'));

    return dispatch({
      type: SELECT_PROJECT,
      payload: {id}
    })
  }
}


export function fetchFeatures() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_FEATURES,

      fetch('/features_list')
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(receiveFeatures(json.data))
          } else {
            dispatch(
              showNotification(
                'Error downloading features ({})'.format(json.message)
              ));
          }
          return json;
        }
        ).catch(ex => console.log('fetchFeatures exception:', ex))
    )
}

// Receive list of featuresets
function receiveFeatures(features) {
  return {
    type: RECEIVE_FEATURES,
    payload: features,
  }
}


export function computeFeatures(form) {
  return dispatch =>
    promiseAction(
      dispatch,
      COMPUTE_FEATURES,

      fetch('/features',
            {method: 'POST',
             body: JSON.stringify(form),
             headers: new Headers({
               'Content-Type': 'application/json'
             })}
      ).then(response => response.json()
      ).then(json => {
        if (json.status == 'success') {
          dispatch(resetForm('featurize'));
          dispatch(showNotification('Successfully computed feature set'));
          dispatch(hideExpander('featsetFormExpander'));
        } else {
          return Promise.reject({_error: json.message});
        }
        return json;
      })
    )
}


export function deleteFeatureset(id) {
  return dispatch =>
    promiseAction(
      dispatch,
      DELETE_FEATURESET,

      fetch('/features/' + id, {method: 'DELETE'})
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(showNotification('Feature set successfully deleted'));
          } else {
            dispatch(
              showNotification(
                'Error deleting feature set ({})'.format(json.message)
              ));
          }
        })
  )
}


export function fetchSklearnModels() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_SKLEARN_MODELS,

      fetch('/sklearn_models')
        .then(response => response.json())
        .then(json => {
          if (json.status == 'success') {
            dispatch(receiveSklearnModels(json.data))
          } else {
            dispatch(
              showNotification(
                'Error downloading sklearn models ({})'.format(json.message)
              ));
          }
          return json;
        }
        ).catch(ex => console.log('fetchSklearnModels exception:', ex))
      )
}

function receiveSklearnModels(sklearn_models) {
  return {
    type: RECEIVE_SKLEARN_MODELS,
    payload: sklearn_models
  }
}


// Download models
export function fetchModels() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_MODELS,

      fetch('/models')
        .then(response => response.json())
        .then(json => {
          return dispatch(receiveModels(json.data))
        }
        ).catch(ex => console.log('fetchModels', ex))
    )
}

// Receive list of models
function receiveModels(models) {
  return {
    type: RECEIVE_MODELS,
    payload: models
  }
}


export function doPrediction(form) {
  return dispatch =>
    promiseAction(
      dispatch,
      DO_PREDICTION,

      fetch('/predictions',
            {method: 'POST',
             body: JSON.stringify(form),
             headers: new Headers({
               'Content-Type': 'application/json'
             })}
      ).then(response => response.json()
      ).then(json => {
        if (json.status == 'success') {
          dispatch(resetForm('predict'));
          dispatch(showNotification('Successfully computed model predictions'));
          dispatch(hideExpander('predictFormExpander'));
        } else {
          return Promise.reject({_error: json.message});
        }
        return json;
      })
    )
}


// Download predictions
export function fetchPredictions() {
  return dispatch =>
    promiseAction(
      dispatch,
      FETCH_PREDICTIONS,

      fetch('/predictions')
        .then(response => response.json())
        .then(json => {
          return dispatch(receivePredictions(json.data))
        }
        ).catch(ex => console.log('fetchPredictions', ex))
    )
}

// Receive list of predictions
function receivePredictions(preds) {
  return {
    type: RECEIVE_PREDICTIONS,
    payload: preds
  }
}
