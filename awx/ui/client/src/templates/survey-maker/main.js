import listGenerator from '../../shared/list-generator/main';
import questions from './questions/main';
import surveys from './surveys/main';
import render from './render/main';
import shared from './shared/main';

export default
    angular.module('templates.surveyMaker',
                   [ listGenerator.name,
                     questions.name,
                     surveys.name,
                     render.name,
                     shared.name
                   ]);
