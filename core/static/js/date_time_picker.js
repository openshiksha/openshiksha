$(document).ready(function(){

  if($("#date_assigner").length){
    $(function(){
     $("#assigned_date").pickadate({
          monthSelector: false, // prevents drop downs for month and year picker
          yearSelector: false,
          onStart: function(){    // sets default date as current date
              this.set('select',Date.now())
          },
          min: Date.now(), // prevents user from selecting past dates
      });
     $("#submission_date").pickadate({
          monthSelector: false,
          yearSelector: false,
      });


      var from_input = $('#assigned_date').pickadate();
      var assigned_picker = from_input.pickadate('picker');

      var to_input = $('#submission_date').pickadate();
      var submission_picker = to_input.pickadate('picker');



      // Check if there’s a “from” date to start with.
      if (assigned_picker.get('value') ) {
        submission_picker.set('min', assigned_picker.get('select'));
      }

      // When something is selected, update the "submission” limits.
      assigned_picker.on('set', function(event) {
        if ( event.select ) {
          submission_picker.set('min', assigned_picker.get('select'));    
        }
        else if ( 'clear' in event ) {
          submission_picker.set('min', false);
        }
      })

      $(".time_picker").pickatime({
        format: "HH:i", // puts format in 24 hour clock 
        interval: 240,// sets interval to every 4 hours
        disable:[ // disables all values except one for selection
          true,
          [20,0],
        ],
      });
    });
  }

});



      