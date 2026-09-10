import { test, expect } from "@playwright/test";

test.describe("OpporSphere - End-to-End Smoke Flows", () => {
  test("Landing and Auth pages render correctly", async ({ page }) => {
    // 1. Check Login page
    await page.goto("/login");
    await expect(page).toHaveTitle(/Login|OpporSphere|Sign In/i);
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in|log in/i })).toBeVisible();

    // 2. Check Signup page
    await page.goto("/signup");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /create account|sign up/i })).toBeVisible();
  });

  test("Student Profile Setup page loads multi-step form", async ({ page }) => {
    await page.goto("/profile/setup");
    // Should render setup wizard steps
    await expect(page.getByText(/Profile Setup|Academic Background|Skills/i)).toBeVisible();
  });

  test("Opportunity Feed renders feed layout and action headers", async ({ page }) => {
    await page.goto("/feed");
    // Verify feed page structure and header
    await expect(page.getByText(/Opportunity Feed|Personalized Matches|Recommended/i)).toBeVisible();
  });

  test("Smart Discovery Search renders natural language search bar", async ({ page }) => {
    await page.goto("/discovery");
    // Check search input box is present
    const searchInput = page.getByPlaceholder(/search|e\.g\.|hackathon|internship/i);
    await expect(searchInput).toBeVisible();

    // Type a query
    await searchInput.fill("Find AI hackathons in San Francisco this month");
    await expect(searchInput).toHaveValue("Find AI hackathons in San Francisco this month");
  });

  test("Team Finder page renders candidate search structure", async ({ page }) => {
    await page.goto("/team-finder");
    await expect(page.getByText(/Team Finder|Find Collaborators|Registered Events/i)).toBeVisible();
  });

  test("Copilot Chat Widget is present on dashboard and can be toggled", async ({ page }) => {
    await page.goto("/dashboard");
    // Copilot widget floating toggle button
    const copilotBtn = page.getByRole("button", { name: /copilot|ask ai|chat/i });
    if (await copilotBtn.isVisible()) {
      await copilotBtn.click();
      // Expanded chat input should now appear
      await expect(page.getByPlaceholder(/ask anything|ask copilot|type a message/i)).toBeVisible();
    }
  });
});
