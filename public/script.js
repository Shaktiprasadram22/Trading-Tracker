document.addEventListener("DOMContentLoaded", function () {
  // Load entries when the page is fully loaded
  loadEntries();

  // Handle form submission for new or updated entries
  document
    .getElementById("inputForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();

      const entryData = {
        date: document.getElementById("date").value,
        stock: document.getElementById("stock").value,
        volumeMin: parseInt(document.getElementById("volumeMin").value, 10),
        entryPrice: parseFloat(document.getElementById("entryPrice").value),
        decision: document.getElementById("decision").value,
        stopLoss: parseFloat(document.getElementById("stopLoss").value),
        target: parseFloat(document.getElementById("target").value),
        premium: document.getElementById("premium").value,
        putCall: document.getElementById("putCall").value,
        success: document.getElementById("success").value,
        remark: document.getElementById("remark").value,
      };

      const editIndex = document.getElementById("editIndex").value; // This should be set when editing an entry

      // Determine the appropriate URL and HTTP method
      const url = editIndex ? `/api/entries/${editIndex}` : "/api/entries";
      const method = editIndex ? "PUT" : "POST";

      // Send the data to the server
      fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(entryData),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              "Network response was not ok " + response.statusText
            );
          }
          return response.json();
        })
        .then((data) => {
          alert("Entry saved successfully!");
          loadEntries(); // Reload entries to update the table
          document.getElementById("inputForm").reset(); // Reset the form
          document.getElementById("editIndex").value = ""; // Clear the index
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Error saving entry: " + error.message);
        });
    });
});

// Function to load all entries and display them
function loadEntries() {
  fetch("/api/entries")
    .then((response) => response.json())
    .then((entries) => {
      const tableBody = document
        .getElementById("summaryTable")
        .getElementsByTagName("tbody")[0];
      tableBody.innerHTML = ""; // Clear existing entries
      entries.forEach((entry, index) => {
        const row = tableBody.insertRow();
        Object.keys(entry).forEach((key) => {
          const cell = row.insertCell();
          cell.textContent = entry[key];
        });
        // Add action buttons
        const actionsCell = row.insertCell();
        actionsCell.innerHTML = `<button onclick="editEntry(${index})">Edit</button>
                                 <button onclick="deleteEntry(${index})">Delete</button>`;
      });
    })
    .catch((error) => console.error("Error loading entries:", error));
}

// Function to edit an entry
function editEntry(index) {
  fetch(`/api/entries/${index}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("HTTP status " + response.status);
      }
      return response.json();
    })
    .then((entry) => {
      document.getElementById("date").value = entry.date || "";
      document.getElementById("stock").value = entry.stock || "";
      document.getElementById("volumeMin").value = entry.volumeMin || 0;
      document.getElementById("entryPrice").value = entry.entryPrice || 0.0;
      document.getElementById("decision").value = entry.decision || "Buy";
      document.getElementById("stopLoss").value = entry.stopLoss || 0.0;
      document.getElementById("target").value = entry.target || 0.0;
      document.getElementById("premium").value = entry.premium || "";
      document.getElementById("putCall").value = entry.putCall || "Call";
      document.getElementById("success").value = entry.success || "Yes";
      document.getElementById("remark").value = entry.remark || "";

      document.getElementById("editIndex").value = index; // Set the index for update
      document.getElementById("daily-input").scrollIntoView(); // Navigate to Daily Input section
    })
    .catch((error) => {
      console.error("Error fetching entry:", error);
      alert("Error fetching entry: " + error.message);
    });
}

// Function to delete an entry
function deleteEntry(index) {
  if (confirm("Are you sure you want to delete this entry?")) {
    fetch(`/api/entries/${index}`, {
      method: "DELETE",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to delete entry");
        }
        loadEntries(); // Reload to update the UI
      })
      .catch((error) => {
        console.error("Error deleting entry:", error);
        alert("Error deleting entry: " + error.message);
      });
  }
}

document
  .getElementById("analyzeSuccessRate")
  .addEventListener("click", function () {
    fetch("/api/entries")
      .then((response) => response.json())
      .then((entries) => {
        let totalEntries = entries.length;
        let successfulEntries = entries.filter(
          (entry) => entry.success === "Yes"
        ).length;
        let successRate = 0;
        if (totalEntries > 0) {
          successRate = ((successfulEntries / totalEntries) * 100).toFixed(2);
        }
        document.getElementById(
          "successRateDisplay"
        ).innerText = `${successRate}% success rate based on ${totalEntries} entries.`;
      })
      .catch((error) => {
        console.error("Error loading entries:", error);
        alert("Failed to calculate success rate");
      });
  });
