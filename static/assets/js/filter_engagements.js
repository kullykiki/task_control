document.addEventListener('DOMContentLoaded', function () {
     fetchInitialData();
});

function fetchInitialData() {
     fetchEngagementData('/taskcontrol/search_filter_engagement_details/');
}

function fetchEngagementData(url) {
     fetch(url)
          .then(response => {
               if (!response.ok) {
                    throw new Error('Network response was not ok');
               }
               return response.json();
          })
          .then(data => {
               displayEngagements(data);
          })
          .catch(error => {
               displayError('Error fetching initial engagements: ' + error.message);
          });
}

function displayEngagements(data) {
     var tbody = document.getElementById('engagementDataBody');
     tbody.innerHTML = '';

     if (data.engagements && data.engagements.length > 0) {
          data.engagements.forEach(function (engagement) {
               var newRow = tbody.insertRow();
               newRow.innerHTML = `
<td>${engagement.job_code}</td>
<td>${engagement.type}</td>
<td>${engagement.reviewer}</td>
<td>${engagement.approver}</td>
<td>${engagement.administrator}</td>
<td>${engagement.deadline}</td>
<td>${engagement.status}</td>
`;
          });
     } else {
          displayError('No engagements found.');
     }
}

function displayError(message) {
     var tbody = document.getElementById('engagementDataBody');
     tbody.innerHTML = `<tr>
<td colspan="7">${message}</td>
</tr>`;
}

document.getElementById('filterForm').addEventListener('submit', function (event) {
     event.preventDefault();
     var formData = new FormData(this);
     var searchParams = new URLSearchParams(formData).toString();

     fetchEngagementData('/taskcontrol/get_filter_engagement_details/?' + searchParams);
});