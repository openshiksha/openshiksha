function draw_subjectroom_assignment_performance(arraydata, topic, assignment_data) {
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Full Name');
        data.addColumn('number', 'Score');
        data.addRows(arraydata);
        
        var options = {
          title: topic,
          height:CHART_HEIGHT,
          width: CHART_WIDTH,
          legend: { 
            position: 'none' 
          },
          hAxis:{
              title: "Score",
            viewWindowMode: 'Explicit',
            viewWindow: {
                max: 101,
                min: 0,
            },
            ticks: [0,10,20,30,40,50,60,70,80,90,100] // to keep xaxis fixed
          },
          vAxis:{
            title:"Number of students",
            viewWindow: {
                min: 0
            }
          },
          histogram: { 
            bucketSize:10 
          },
          colors:["#e7711c"]
        };
    var chart = new google.visualization.Histogram(document.getElementById('subjectroom_assignment_histogram'));
        chart.draw(data, options);

        google.visualization.events.addListener(chart, 'select', function() {
            // grab a few details before redirecting
  
          var selection = chart.getSelection();
          chart.setSelection(); // to remove the selection from the chart element
          var row = selection[0].row;
          var col = selection[0].column;
         
      
          if (col==1){
              var submission_id = assignment_data[row].submission_id;
              if (submission_id) {    // only redirect for non-anonymized histogram elements
                  window.location.href = "/submission/" + submission_id;
                  alert("Redirecting Page to Assignment Submission");
              }
          }
        });
}


  
