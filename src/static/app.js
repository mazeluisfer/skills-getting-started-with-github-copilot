document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      
      // Clear and repopulate select dropdown
      activitySelect.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Create activity card HTML with participant list
        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <p><strong>Participants:</strong></p>
            ${details.participants.length > 0 
              ? `<ul class="participants-list">
                  ${details.participants.map(email => `
                    <li>
                      <span class="participant-email">${email}</span>
                      <button class="delete-btn" data-activity="${name}" data-email="${email}" title="Remove participant">
                        ✕
                      </button>
                    </li>
                  `).join('')}
                 </ul>` 
              : '<p class="no-participants">No participants yet. Be the first to sign up!</p>'}
          </div>
        `;

        // Add delete button event listeners
        activityCard.querySelectorAll('.delete-btn').forEach(btn => {
          btn.addEventListener('click', async (e) => {
            const activityName = e.target.getAttribute('data-activity');
            const email = e.target.getAttribute('data-email');
            
            if (confirm(`Remove ${email} from ${activityName}?`)) {
              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(activityName)}/participants/${encodeURIComponent(email)}`,
                  { method: 'DELETE' }
                );
                
                if (response.ok) {
                  // Refresh activities to update the list
                  fetchActivities();
                  messageDiv.textContent = `Successfully removed ${email} from ${activityName}`;
                  messageDiv.className = 'success';
                  messageDiv.classList.remove('hidden');
                  setTimeout(() => messageDiv.classList.add('hidden'), 5000);
                } else {
                  const result = await response.json();
                  messageDiv.textContent = result.detail || 'Failed to remove participant';
                  messageDiv.className = 'error';
                  messageDiv.classList.remove('hidden');
                }
              } catch (error) {
                console.error('Error removing participant:', error);
                messageDiv.textContent = 'Failed to remove participant. Please try again.';
                messageDiv.className = 'error';
                messageDiv.classList.remove('hidden');
              }
            }
          });
        });

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Reload activities to update participant lists
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
