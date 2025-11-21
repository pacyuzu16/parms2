function updateProgressBars() {
    const progressBars = document.querySelectorAll(".progress-bar");
    progressBars.forEach(bar => {
        const progressValue = bar.getAttribute("data-value");
        bar.style.width = `${progressValue}%`;
    });
}

// Call this function after the page loads
document.addEventListener("DOMContentLoaded", updateProgressBars);


async function fetchDashboardData() {
    try {
        const response = await fetch("/api/dashboard-data/");
        const data = await response.json();

        // Update user count
        document.querySelector("#userCount").textContent = data.users;

        // Update card values dynamically
        document.querySelector("#parkingCount").textContent = data.parkings;
        document.querySelector("#carCount").textContent = data.cars;
    } catch (error) {
        console.error("Error fetching dashboard data:", error);
    }
}

// Fetch data on page load
document.addEventListener("DOMContentLoaded", fetchDashboardData);
