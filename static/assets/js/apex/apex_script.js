Apex.grid = {
  padding: {
    right: 0,
    left: 0
  }
}

Apex.dataLabels = {
  enabled: false
}

var randomizeArray = function (arg) {
  var array = arg.slice();
  var currentIndex = array.length, temporaryValue, randomIndex;

  while (0 !== currentIndex) {

    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

var sparklineData = [47, 45, 54, 38, 56, 24, 65, 31, 37, 39, 62, 51, 35, 41, 35, 27, 93, 53, 61, 27, 54, 43, 19, 46];

// the default colorPalette for this dashboard
//var colorPalette = ['#01BFD6', '#5564BE', '#F7A600', '#EDCD24', '#F74F58'];
var colorPalette = ['#00D8B6', '#008FFB', '#FEB019', '#FF4560', '#775DD0']


// Donut
var optionPie = {
  chart: {
    type: 'pie',
    width: '100%',
    height: 400
  },
  dataLabels: {
    enabled: false,
  },
  plotOptions: {
    pie: {
      customScale: 0.8,
      pie: {
        size: '85%',
      },
      offsetY: 20,
    },
    stroke: {
      colors: undefined
    }
  },
  colors: colorPalette,
  title: {
    text: 'Tasks Controller',
    style: {
      fontSize: '18px'
    }
  },
  series: [30, 20, 50, 30, 80],
  labels: ['สำเร็จ', 'รอลูกค้า', 'รอตรวจสอบ', 'กำลังดำเนินงาน', 'เปิดงาน'],
  legend: {
    position: 'right',
    offsetY: 80
  }
}

var total = optionPie.series.reduce(function(a, b) {
  return a + b;
}, 0);

// นำผลรวมไปใส่ใน title.text
optionPie.title.text += ' - รวมทั้งสิ้น: ' + total;

var pie = new ApexCharts(
  document.querySelector("#pie"),
  optionPie
)
pie.render();

document.getElementById('total-value').innerText = total;

function trigoSeries(cnt, strength) {
  var data = [];
  for (var i = 0; i < cnt; i++) {
    data.push((Math.sin(i / strength) * (i / strength) + i / strength + 1) * (strength * 2));
  }

  return data;
}


// a small hack to extend height in website sample dashboard
chartLine.render().then(function () {
  var ifr = document.querySelector("#wrapper");
  if (ifr.contentDocument) {
    ifr.style.height = ifr.contentDocument.body.scrollHeight + 20 + 'px';
  }
});


// on smaller screen, change the legends position for donut
var mobileDonut = function () {
  if ($(window).width() < 768) {
    donut.updateOptions({
      plotOptions: {
        pie: {
          offsetY: -15,
        }
      },
      legend: {
        position: 'bottom'
      }
    }, false, false)
  }
  else {
    donut.updateOptions({
      plotOptions: {
        pie: {
          offsetY: 20,
        }
      },
      legend: {
        position: 'left'
      }
    }, false, false)
  }
}

$(window).resize(function () {
  mobileDonut()
});