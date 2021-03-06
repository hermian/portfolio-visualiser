var availableFields = {};

//  COOOOOOOKIES
function getCookie(name)
{
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for(i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + "=")) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}
// Cookies and csrf
var csrftoken = getCookie("csrftoken");
function csrfSafeMethod(method)
{
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

/*  Adds a new column to the correct table  */
function addColClick(pid) {
  var fields = availableFields[pid],
      lastTds = $('#'+pid+'-tablebody').children('tr').children('td:last-child'),
      numberInput = $('<input>').attr('class', 'text-center new-mile-field-'+pid)
                                .attr('type', 'number')
                                .attr('step', 0.01);
  $.each(lastTds, function(idx, td) {
    $('<td>').insertAfter(td);
  });
  $('#'+pid+'-tablebody').children('tr')
                         .children('td:last-child')
                         .last()
                         .append(numberInput);

  var select = $('<select>').attr('class', 'text-center')
                            .attr('id', 'new-col-name-'+pid);
  $.each(fields, function(id, name) {
    select.append($('<option>').attr('value', id).append(name));
  });
  numberInput.attr('name', Object.keys(fields)[0]);

  var lastTh = $('#'+pid+'-tablehead').children('tr:last-child').children('th:last-child');
  $('<th>').append(select).insertAfter(lastTh);
  select.change(function() {
    numberInput.attr('name', $(this).val());
  });
}

function lockColClick(pid) {
  var select = $('#new-col-name-'+pid),
      selectText = $('#new-col-name-'+pid+' :selected').text();

  select.parents('th').attr('data-dimid', select.val()).append(selectText);
  select.remove();
  delete availableFields[pid][select.val()];
  if (Object.keys(availableFields[pid]).length <= 0) {
    $('#add-col-btn-'+pid).remove();
  }
}

function checkRows(pid) {
  var inputs = $('.new-mile-field-' + pid),
      text = "",
      errorFree = true;

  inputs.each(function() {
    if($(this).val() == '') {
      errorFree = false;
      text = "Please fill in all the fields";
    }
  });

  var lastTh = $('#'+pid+'-tablehead').children('tr').children('th').last();
  if(lastTh.children('select').length > 0) {
    errorFree = false;
    text = "Please lock new fields or refresh to remove them";
  }

  return [errorFree, text];
}

function submitRow(pid) {
  var inputs = $('.new-mile-field-' + pid),
      ajaxdata = {'pid': pid};

  inputs.each(function() {
    ajaxdata[$(this)[0].name] = $(this).val();
  });

  $.ajax({
    method: "POST",
    url: "/manage/milestone",
    data: ajaxdata,
    error: function() {
      alert("Milestone wasn't saved! Refresh page to see all saved milestones!");
    }
  });
}

function inputsToCells(pid) {
  var inputs = $(".new-mile-field-" + pid);
  inputs.each(function() {
    if ($(this)[0].type == 'date') {  // Date needs to be formatted
      var dateparts = $(this).val().split("-"),
          datestr = dateparts.reverse().join('/');
      $(this).parent().html(datestr);
    }
    else {
      $(this).parent().html($(this).val());
    }
  });
}

function addClick(btn){
  var pid = $(btn).data('pid'),
    tablebody = $('#' + pid + "-tablebody"),
    inputClass = 'text-center new-mile-field-' + pid,
    due_date_cell = $('<input>').attr('name', 'due_date')
                                .attr('class', inputClass)
                                .attr('type', 'date'),
    row = $('<tr>').append($('<td>').append(due_date_cell)),
    ths = $('#' + pid + '-tablehead').children('tr').children();

  /*  Add the form row  */
  $.each(ths, function(idx, th) {
    if( th.innerText != '') {
      row.append($('<td>').append($('<input>')
                           .attr('name', th.dataset.dimid)
                           .attr('class', inputClass)
                           .attr('type', 'number')
                           .attr('step', 0.01)));
    }
  });
  tablebody.append(row);

  /*  Hide them and then slide them out  */
  row.children()
     .wrapInner('<div style="display:none;"></div>')
     .parent()
     .find('td > div')
     .slideDown(100);

  $(btn).toggleClass('submit');
  $(btn).children('.icons').toggleClass('icons-active');


  /*  ADD COL STUFF  */
  /*  Gather the existing fields  */
  var ths = $('#'+pid+'-tablehead').children('tr').children(),
      existingMileFields = [];
  $.each(ths, function(idx, th) {
    var id = th.dataset.dimid;
    if(id != undefined) {
      existingMileFields.push(parseInt(id));
    }
  });

  /*  Get the alternatives for new fields  */
  $.ajax({
    method: "GET",
    url: "/get/"+pid+"/fields/",
    data: {'existing': JSON.stringify(existingMileFields)},
    success: function(fields){
      availableFields[pid] = fields.fields;
      if(Object.keys(availableFields[pid]).length > 0) {
        var plus = $('<span>').attr('class', 'icons')
                              .append($('<span>').attr('class', 'vertical'))
                              .append($('<span>').attr('class', 'horizontal')),
            button = $('<button>').attr('type', 'button')
                                  .attr('class', 'btn btn-success add-col-btn')
                                  .attr('id', 'add-col-btn-'+pid)
                                  .append(plus);
        tablebody.append(button);
        button.click(function(e) {
          /*  When you add the col  */
          if(!$(e.target).hasClass('lockcol')) {
            addColClick(pid);
          }
          /*  When you lock it in  */
          else {
            lockColClick(pid);
          }
          $(this).children('.icons').toggleClass('icons-active');
          $(this).toggleClass('lockcol');
        });
      }
    }
  });
}

function submitClick(btn) {
  var pid = $(btn).data('pid'),
      checkRowsResult = checkRows(pid);

  if(checkRowsResult[0]) {
    submitRow(pid);
    inputsToCells(pid);

    $(btn).toggleClass('submit');
    $(btn).children('.icons').toggleClass('icons-active');
    $('#add-col-btn-'+pid).remove();
  }
  else {
    alert(checkRowsResult[1]);
  }
}

$(function(){
  $(".add-row-btn").click(function(e){
    if (!$(e.target).hasClass('submit')) {
      addClick(e.target);
    }
    else {
      submitClick(e.target);
    }
  });
});
