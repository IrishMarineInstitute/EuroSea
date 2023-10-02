function myFunction(x) {
  if (x.matches) { 
    
                   let layout = {
                       width: 1000, height: 815, showlegend: false,
                       title: {
                           text: '',
                           font: {size: 16,},
                       },
                       xaxis: {
                           zeroline: false, mirror: true, showline: true,
                           ticks: 'outside', tickvals: [0, 1, 2, 3, 4], ticktext: ['0º', '1ºE', '2ºE', '3ºE', '4ºE'],
                           automargin: true, range: [-0.91, 4.51],
                       },
                       yaxis: {
                           mirror: true, showline: true,
                           ticks: 'outside', tickvals: [38, 39, 40, 41], ticktext: ['38ºN', '39ºN', '40ºN', '41ºN'],
                           range: [37.59, 41.01],
                       },
                       font: {family: 'Sans-Serif', size: 16,},
                       coloraxis: {
                           colorbar: {
                               tickvals: [0, 0.5, 1, 1.5, 2], ticktext: ['0.0', '0.5', '1.0', '1.5', '2.0'],
                           },
                       },
                   };

  } else {
    let layout = {};
  }
}

function get_layout() {
    var x = window.matchMedia("(min-width: 720px)")
    myFunction(x) // Call listener function at run time
    x.addListener(myFunction) // Attach listener function on state changes
}
