// Functions to display date and time
function display_c() {
   var refresh=1000;
   mytime = setTimeout('display_ct()', refresh)
}
function display_ct() {
   var b = 'Deenish Island on ';
   var x = new Date();
   x.setDate(x.getDate() - 120);
   var x = x.toUTCString();
   document.getElementById('time').value = b.concat(x);
   display_c();
}

// Function to set MHW warnings
function mhw_strcolor(string, ID) {
        const input = document.getElementById(ID);
        var temperature = parseFloat(string).toFixed(2)
        if ( temperature >= 5 ) {
            input.style.backgroundColor = "#FF0000"
        } else {
            input.style.backgroundColor = "#D3D3D3"
        }
     }
     
// Function to set color warnings depending on temperature
function temperature_strcolor(string, ID) {
        const input = document.getElementById(ID);
        var temperature = parseFloat(string).toFixed(2)
        if ( isNaN(temperature) ) {
            input.style.backgroundColor = "#9E9E9E"
            input.value = "N/D"
        } else if ( temperature >= 30 ) {
            input.style.backgroundColor = "#FF0000"
        } else {
            input.style.backgroundColor = "#39E75F"
        }
     }
     
// Function to set wave height color warnings
function wh_strcolor(string, ID) {
        const input = document.getElementById(ID);
        var wh = parseFloat(string).toFixed(2)
        if ( isNaN(wh) ) {
            input.style.backgroundColor = "#9E9E9E"
            input.value = "N/D"
        } else if ( wh >= 3 ) {
            input.style.backgroundColor = "#FF0000"
        } else if ( wh >= 2 ) {
            input.style.backgroundColor = "#FC6A03"
        } else {
            input.style.backgroundColor = "#39E75F"
        }
     }
     
// Function to set color warnings depending on oxygen
function oxygen_strcolor(string, ID) {
        const input = document.getElementById(ID);
        var oxygen = parseFloat(string).toFixed(2)
        if ( isNaN(oxygen) ) {
            input.style.backgroundColor = "#9E9E9E"
            input.value = "N/D"
        } else if ( oxygen < 70 ) {
            input.style.backgroundColor = "#FF0000"
        } else {
            input.style.backgroundColor = "#39E75F"
        }
     }
     
// Function to set color warnings for Extreme Marine Events
function marine_warning(string, ID) {
        const input = document.getElementById(ID);
        var status = parseInt(string)
        if ( status ) {
            input.style.color = "#000000"
            input.style.backgroundColor = "#FF0000"
        }
}

// Run everything
function init() {

   var str = document.getElementById("latest-temperature-value").content
   temperature_strcolor(str, "latest-temperature")

   var str = document.getElementById("latest-oxygen-value").content
   oxygen_strcolor(str, "latest-oxygen")

   var str = document.getElementById("significant-wave-height-value").content
   wh_strcolor(str, "latest-swh")
   wh_strcolor(str, "latest-swh-mobile")

   var str = document.getElementById("forecast-max-swh-value").content
   wh_strcolor(str, "max-swh-fc")
   wh_strcolor(str, "max-swh-fc-mobile")

   var str = document.getElementById("swell-value").content
   wh_strcolor(str, "latest-swell")

   var str = document.getElementById("forecast-max-swell-value").content
   wh_strcolor(str, "max-swell-fc")

}
