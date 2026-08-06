document.addEventListener('DOMContentLoaded', function () {
  var principalInput = document.getElementById('calc-principal');
  if (!principalInput) return;

  var timeInput = document.getElementById('calc-time');
  var rateInput = document.getElementById('calc-rate');
  var compoundInputs = document.getElementsByName('calc-compound');

  var principalValueEl = document.getElementById('calc-principal-value');
  var timeValueEl = document.getElementById('calc-time-value');
  var rateValueEl = document.getElementById('calc-rate-value');
  var resultTimeEl = document.getElementById('calc-result-time');
  var resultTotalEl = document.getElementById('calc-result-total');
  var resultPrincipalEl = document.getElementById('calc-result-principal');
  var resultInterestEl = document.getElementById('calc-result-interest');

  function formatKES(amount) {
    return 'KES ' + Math.round(amount).toLocaleString('en-KE');
  }

  function compoundFrequency() {
    for (var i = 0; i < compoundInputs.length; i++) {
      if (compoundInputs[i].checked) return parseInt(compoundInputs[i].value, 10);
    }
    return 1;
  }

  function update() {
    var principal = parseFloat(principalInput.value);
    var years = parseFloat(timeInput.value);
    var ratePercent = parseFloat(rateInput.value);
    var n = compoundFrequency();
    var isMonthly = n === 12;

    var periodicRate = ratePercent / 100;
    var periods = isMonthly ? years * 12 : years;
    var total = principal * Math.pow(1 + periodicRate, periods);
    var interestEarned = total - principal;

    principalValueEl.textContent = formatKES(principal);
    timeValueEl.textContent = years + (years === 1 ? ' year' : ' years');
    rateValueEl.textContent = ratePercent + '% ' + (isMonthly ? 'per month' : 'per year');

    resultTimeEl.textContent = years;
    resultTotalEl.textContent = formatKES(total);
    resultPrincipalEl.textContent = formatKES(principal);
    resultInterestEl.textContent = formatKES(interestEarned);
  }

  [principalInput, timeInput, rateInput].forEach(function (input) {
    input.addEventListener('input', update);
  });
  for (var j = 0; j < compoundInputs.length; j++) {
    compoundInputs[j].addEventListener('change', update);
  }

  update();
});
