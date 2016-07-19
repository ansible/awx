/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

$(function() {

  // Add syntax highlighting to examples in description.
  $('.description pre').addClass('prettyprint');
  prettyPrint();

  // Make links from relative URLs to resources.
  $('span.str').each(function() {
    var s = $(this).html();
    if (s.match(/^\"\/.+\/\"$/) || s.match(/^\"\/.+\/\?.*\"$/)) {
      $(this).html('"<a href=' + s + '>' + s.replace(/\"/g, '') + '</a>"');
    }
  });

  // Make links for all inventory script hosts.
  $('.request-info .pln').filter(function() {
    return $(this).text() === 'script';
  }).each(function() {
    $('.response-info span.str').filter(function() {
      return $(this).text() === '"hosts"';
    }).each(function() {
      $(this).nextUntil('span.pun:contains("]")').filter('span.str').each(function() {
        if ($(this).text().match(/^\".+\"$/)) {
          var s = $(this).text().replace(/\"/g, '');
          $(this).html('"<a href="' + '?host=' + s + '">' + s + '</a>"');
        }
        else if ($(this).text() !== '"') {
          var s = $(this).text();
          $(this).html('<a href="' + '?host=' + s + '">' + s + '</a>');
        }
      });
    });
  });

  // Add classes/icons for dynamically showing/hiding help.
  if ($('.description').html()) {
    $('.description').addClass('prettyprint').parent().css('float', 'none');
    $('.hidden a.hide-description').prependTo('.description');
    $('a.hide-description').click(function() {
      $(this).tooltip('hide');
      $('.description').slideUp('fast');
      return false;
    });
    $('.hidden a.toggle-description').appendTo('.page-header h1');
    $('a.toggle-description').click(function() {
      $(this).tooltip('hide');
      $('.description').slideToggle('fast');
      return false;
    });
  }

  $('[data-toggle="tooltip"]').tooltip();

  if ($(window).scrollTop() >= 115) {
    $('body').addClass('show-title');
  }
  $(window).scroll(function() {
    if ($(window).scrollTop() >= 115) {
      $('body').addClass('show-title');
    }
    else {
      $('body').removeClass('show-title');
    }
  });

  $('a.resize').click(function() {
    $(this).tooltip('hide');
    if ($(this).find('span.glyphicon-resize-full').size()) {
      $(this).find('span.glyphicon').addClass('glyphicon-resize-small').removeClass('glyphicon-resize-full');
      $('.container').addClass('container-fluid').removeClass('container');
      document.cookie = 'api_width=wide; path=/api/';
    }
    else {
      $(this).find('span.glyphicon').addClass('glyphicon-resize-full').removeClass('glyphicon-resize-small');
      $('.container-fluid').addClass('container').removeClass('container-fluid');
      document.cookie = 'api_width=fixed; path=/api/';
    }
    return false;
  });

  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length == 2) return parts.pop().split(";").shift();
  }
  if (getCookie('api_width') == 'wide') {
    $('a.resize').click();
  }

});
