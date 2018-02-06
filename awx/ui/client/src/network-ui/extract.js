#!/usr/bin/env node
var YAML = require('yamljs');

function Iterator(o){
    var k=Object.keys(o);
    return {
        next:function(){
            return k.shift();
        }
    };
}

var myArgs = process.argv.slice(2);
var implementation = require(myArgs[0]);
var states = [];
var transitions = [];
var data = {states: states,
            transitions: transitions};

var state_iter = Iterator(implementation);
var transition_iter = null;
var next_state = state_iter.next();
var next_transition = null;
var state = null;
var transition = null;
var i = 0;
while(next_state !== undefined) {
    state = implementation[next_state];
    transition_iter = Iterator(state.constructor.prototype);
    next_transition = transition_iter.next();
    while (next_transition !== undefined) {
        transition = state.constructor.prototype[next_transition];
        if (transition.transitions !== undefined) {
            for (i = 0; i < transition.transitions.length; i++) {
                transitions.push({from_state: next_state,
                                  to_state:transition.transitions[i],
                                  label:next_transition});
            }
        }
        next_transition = transition_iter.next();
    }
    states.push({label: state.name});
    next_state = state_iter.next();
}


console.log(YAML.stringify(data));
