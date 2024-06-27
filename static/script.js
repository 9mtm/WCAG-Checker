document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const fileInput = document.getElementById('file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        document.getElementById('results-container').style.display = 'block';
        document.getElementById('filename').textContent = fileInput.files[0].name;
        document.getElementById('title').textContent = data.metadata['/Title'] || 'N/A';
        document.getElementById('language').textContent = data.natural_language ? 'Yes' : 'No';
        document.getElementById('tags').textContent = data.tags ? 'Yes' : 'No';
        document.getElementById('pages').textContent = data.metadata['/PageCount'] || 'N/A';
        document.getElementById('size').textContent = `${(fileInput.files[0].size / 1024).toFixed(2)} KB`;

        const updateResults = (id, passed, warned, failed) => {
            document.getElementById(`${id}-passed`).textContent = passed;
            document.getElementById(`${id}-warned`).textContent = warned;
            document.getElementById(`${id}-failed`).textContent = failed;
        };

        updateResults('pdf-syntax', data.text_extracted ? 1 : 0, 0, data.text_extracted ? 0 : 1);
        updateResults('fonts', Object.values(data.fonts_embedded).filter(val => val).length, 0, Object.values(data.fonts_embedded).filter(val => !val).length);
        updateResults('content', data.alt_texts ? 1 : 0, 0, data.alt_texts ? 0 : 1);
        updateResults('embedded-files', 0, 0, 0); // Assuming no check for embedded files in your code
        updateResults('natural-language', data.natural_language ? 1 : 0, 0, data.natural_language ? 0 : 1);
        updateResults('structure-elements', data.structure_elements ? 1 : 0, 0, data.structure_elements ? 0 : 1);
        updateResults('structure-tree', 0, 0, 0); // Assuming no check for structure tree in your code
        updateResults('role-mapping', data.role_mapping ? 1 : 0, 0, data.role_mapping ? 0 : 1);
        updateResults('alternate-descriptions', Object.values(data.alt_texts).some(page => page.length) ? 1 : 0, 0, Object.values(data.alt_texts).some(page => page.length) ? 0 : 1);
        updateResults('metadata', data.metadata ? 1 : 0, 0, data.metadata ? 0 : 1);
        updateResults('document-settings', 0, 0, 0); // Assuming no check for document settings in your code
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the file.');
    });
});


function updateDemoColors(colorFront, colorBack) {
    const demo = document.querySelector("#sample-text");
    demo.style.color = `rgb(${colorFront.toString()})`;
    demo.style.backgroundColor = `rgb(${colorBack.toString()})`;
  }
  
  /* the following functions are adapted from https://stackoverflow.com/a/9733420/3695983 */
  function luminanace(r, g, b) {
    var a = [r, g, b].map(function (v) {
      v /= 255;
      return v <= 0.03928
        ? v / 12.92
      : Math.pow( (v + 0.055) / 1.055, 2.4 );
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }
  function contrast(rgb1, rgb2) {
    const luminanceFront = luminanace(rgb1[0], rgb1[1], rgb1[2]);
    const luminanceBack  = luminanace(rgb2[0], rgb2[1], rgb2[2]);
    return luminanceBack > luminanceFront 
      ? ((luminanceFront + 0.05) / (luminanceBack + 0.05))
      : ((luminanceBack + 0.05) / (luminanceFront + 0.05));
  }
  
  function updateBoxesColors(colorFront, colorBack) {
    const ratio = contrast(colorFront, colorBack);
    document.querySelector("#aa-normal").className  = ratio < 0.22222 ? "" : "fail";
    document.querySelector("#aa-large").className   = ratio < 0.33333 ? "" : "fail";
    document.querySelector("#aaa-normal").className = ratio < 0.14285 ? "" : "fail";
    document.querySelector("#aaa-large").className  = ratio < 0.22222 ? "" : "fail";
    
    const totalWrong = document.querySelectorAll(".fail").length;
    let mouth = document.querySelector("#mouth");
    let smile = document.querySelector("#smile");
    
    switch(totalWrong) {
      case 0:
        mouth.setAttribute("d", "M 106,132 C 113,127 125,128 125,132 125,128 137,127 144,132 141,142  134,149  125,149  116,149 109,142 106,132 Z");
        smile.setAttribute("d", "M125,144 C 140,144 143,132 143,132 143,132 125,133 125,133 125,133 106.5,132 106.5,132 106.5,132 110,144 125,144 Z");
        break;
      case 1:
      case 2:
        mouth.setAttribute("d", "M 106,132 C 113,127 125,128 125,132 125,128 137,127 144,132 141,142  134,146  125,146  116,146 109,142 106,132 Z");
        smile.setAttribute("d", "M125,141 C 140,141 143,132 143,132 143,132 125,133 125,133 125,133 106.5,132 106.5,132 106.5,132 110,141 125,141 Z");
        break;
      case 3: 
        mouth.setAttribute("d", "M 106,132 C 113,127 125,128 125,132 125,128 137,127 144,132 141,138  140,143  125,143  110,143 109,138 106,132 Z");
      smile.setAttribute("d", "M125,138 C 140,138 143.5,132 143.5,132 143.5,132 125,133 125,133 125,133 106.5,132 106.5,132 106.5,132 110,138 125,138 Z");
        break;
      case 4: 
        mouth.setAttribute("d", "M 106,132 C 113,127 125,128 125,132 125,128 137,127 144,132 141,138  134,142  125,142  116,142 109,138 106,132 Z");
        smile.setAttribute("d", "M125,135 C 140,135 143,132 143,132 143,135 125,136 125,136 125,136 106.5,135 106.5,132 106.5,132 110,135 125,135 Z");
        break;
    }
  }
  
  function updateHex(colorFront, colorBack) {
    const colorFrontHex = colorFront.map(function(el) { return Number(el).toString(16).padStart(2, "0").toUpperCase(); });
    const colorBackHex = colorBack.map(function(el) { return Number(el).toString(16).padStart(2, "0").toUpperCase(); });
    document.querySelector("#color-1-hex").value = `#${colorFrontHex.join('')}`;
    document.querySelector("#color-2-hex").value = `#${colorBackHex.join('')}`
  }
  
  function updateColors() {
    const colorFront = [ 
      document.querySelector("#color-1-r").value,
      document.querySelector("#color-1-g").value,
      document.querySelector("#color-1-b").value
    ];
    const colorBack = [
      document.querySelector("#color-2-r").value,
      document.querySelector("#color-2-g").value,
      document.querySelector("#color-2-b").value
    ];
  
    updateDemoColors(colorFront, colorBack);
    updateBoxesColors(colorFront, colorBack);
    updateHex(colorFront, colorBack);
  }
  
  document.querySelectorAll("input[type='number'], input[type='range']").forEach(function(el) {
    el.addEventListener("input", function() {
      if (this.type === "range") {
        this.nextElementSibling.value = this.value;
      } else if (this.type === "number") {
        this.previousElementSibling.value = this.value;
      }
      updateColors();
    });
  });
  
  document.querySelectorAll("input[type='text']").forEach(function(el) {
    el.addEventListener("blur", function() {
      let val = this.value;
      let wrongValue = false;
      if (val[0] === "#") val = val.substring(1);
      if (val.length === 3 || val.length === 6) {
        if (val.length === 3) {
          val = `${val[0]}${val[0]}${val[1]}${val[1]}${val[2]}${val[2]}`;
        }
        if (val.match(/[0-9A-Fa-f]{6}/)) {
          const red = parseInt(`${val[0]}${val[1]}`, 16);
          const green = parseInt(`${val[2]}${val[3]}`, 16);
          const blue = parseInt(`${val[4]}${val[5]}`, 16);
          const target = this.dataset.target;
          
          document.getElementById(`number-${target}-r`).value = red;
          document.getElementById(`number-${target}-g`).value = green;
          document.getElementById(`number-${target}-b`).value = blue;
          document.getElementById(`color-${target}-r`).value = red;
          document.getElementById(`color-${target}-g`).value = green;
          document.getElementById(`color-${target}-b`).value = blue;
          
          updateColors();
        } else {
          wrongValue = true;
        }
      } else {
        wrongValue = true;
      }
      
      if (wrongValue){
        const colorFront = [ 
          document.querySelector("#color-1-r").value,
          document.querySelector("#color-1-g").value,
          document.querySelector("#color-1-b").value
        ];
        const colorBack = [
          document.querySelector("#color-2-r").value,
          document.querySelector("#color-2-g").value,
          document.querySelector("#color-2-b").value
        ];
        updateHex(colorFront, colorBack)
      }
    });
  })


  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll("input[type='checkbox']").forEach(function(el) {
        el.addEventListener("click", function() {
            // logic to update the checklist status and counts
        });
    });

    // apply line-through CSS to checked SCs
    document.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
        checkbox.addEventListener("click", function () {
            this.parentElement.classList.toggle("checked");
        });
    });

    document.querySelectorAll("fieldset input[type='checkbox']").forEach(function (checkbox) {
        checkbox.addEventListener("click", function (e) {
            // logic here modified from: http://3pha.com/wcag2/
            var version2_0 = document.getElementById("wcag20").checked;
            var version2_1 = document.getElementById("wcag21").checked;
            var version2_2 = document.getElementById("wcag22").checked;

            var levelA = document.getElementById("levela").checked;
            var levelAA = document.getElementById("levelaa").checked;
            var levelAAA = document.getElementById("levelaaa").checked;

            // LEVEL A
            if (levelA) {
                document.querySelectorAll(".levela").forEach(el => el.style.display = 'list-item');
                if (!version2_0) document.querySelectorAll(".wcag20").forEach(el => el.style.display = 'none');
                if (!version2_1) document.querySelectorAll(".wcag21").forEach(el => el.style.display = 'none');
                if (!version2_2) document.querySelectorAll(".wcag22").forEach(el => el.style.display = 'none');
            } else {
                document.querySelectorAll(".levela").forEach(el => el.style.display = 'none');
            }

            // LEVEL AA
            if (levelAA) {
                document.querySelectorAll(".levelaa").forEach(el => el.style.display = 'list-item');
                if (!version2_0) document.querySelectorAll(".wcag20").forEach(el => el.style.display = 'none');
                if (!version2_1) document.querySelectorAll(".wcag21").forEach(el => el.style.display = 'none');
                if (!version2_2) document.querySelectorAll(".wcag22").forEach(el => el.style.display = 'none');
            } else {
                document.querySelectorAll(".levelaa").forEach(el => el.style.display = 'none');
            }

            // LEVEL AAA
            if (levelAAA) {
                document.querySelectorAll(".levelaaa").forEach(el => el.style.display = 'list-item');
                if (!version2_0) document.querySelectorAll(".wcag20").forEach(el => el.style.display = 'none');
                if (!version2_1) document.querySelectorAll(".wcag21").forEach(el => el.style.display = 'none');
                if (!version2_2) document.querySelectorAll(".wcag22").forEach(el => el.style.display = 'none');
            } else {
                document.querySelectorAll(".levelaaa").forEach(el => el.style.display = 'none');
            }

            // Count visible SCs and update
            var visibleCount_wcag20 = document.querySelectorAll(".wcag20:visible").length;
            var visibleCount_wcag21 = document.querySelectorAll(".wcag21:visible").length;
            var visibleCount_wcag22 = document.querySelectorAll(".wcag22:visible").length;
            document.getElementById("currentScCount").textContent = visibleCount_wcag20 + visibleCount_wcag21 + visibleCount_wcag22;
        });
    });

    //zebra stripe list items
    document.querySelectorAll("li:nth-child(even)").forEach(function (el) {
        el.classList.add("stripe");
    });
});



