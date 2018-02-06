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
var messages = [];
var data = {messages: messages};
var message_iter = Iterator(implementation);
var field_iter = null;
var next_message = message_iter.next();
var next_field = null;
var message = null;
var message_instance = null;
var fields = null;
// var field = null;
// var i = 0;
while(next_message !== undefined) {
    message = implementation[next_message];
    try {
        message_instance = new message();
    } catch(err) {
        next_message = message_iter.next();
        continue;
    }
    fields = [];
    field_iter = Iterator(message_instance);
    next_field = field_iter.next();
    while (next_field !== undefined) {
        fields.push(next_field);
    //    field = message.constructor.prototype[next_field];
    //    if (field.transitions !== undefined) {
    //        for (i = 0; i < field.transitions.length; i++) {
    //            transitions.push({from_message: next_message,
    //                              to_message:field.transitions[i],
    //                              label:next_field});
    //        }
    //    }
        next_field = field_iter.next();
    }
    if(message_instance.msg_type !== null && message_instance.msg_type !== undefined) {
        messages.push({msg_type: message_instance.msg_type,
                       fields: fields});
    }
    next_message = message_iter.next();
}


console.log(YAML.stringify(data));
