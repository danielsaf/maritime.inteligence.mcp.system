import { test } from '@playwright/test';
import { MapPage } from '../pages/MapPage';

test.describe('Maritime VTS - QA Regression Suite (POM)', () => {
  let mapPage;

  test.beforeEach(async ({ page }) => {
    mapPage = new MapPage(page);
    await mapPage.goto();
  });

  test('should initialize system with map and live connection', async () => {
    await mapPage.expectMapLoaded();
    await mapPage.expectLiveConnection();
  });

  test('should fetch vessels and show operational details on click', async () => {
    await mapPage.clickFirstVessel();
    await mapPage.expectVesselPopupDetails();
  });
});