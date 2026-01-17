# GitHub Secrets Setup for Automated PyPI Publishing

This guide shows how to configure GitHub secrets so the automated PyPI publishing workflow works.

## Required Secrets

You need to add two secrets to your GitHub repository:

1. **PYPI_API_TOKEN** - For publishing to production PyPI
2. **TEST_PYPI_API_TOKEN** - For publishing to Test PyPI (optional)

## Step 1: Get PyPI API Tokens

### Production PyPI Token

1. Go to: https://pypi.org/
2. Log in as `davdunc`
3. Go to **Account Settings** → **API tokens**
4. Click **"Add API token"**
5. Settings:
   - **Token name**: `super-signal-github-actions`
   - **Scope**: Select "Project: super-signal" (if project exists) OR "Entire account" (for first upload)
6. Click **"Add token"**
7. **Copy the token** (starts with `pypi-`) - you won't see it again!

### Test PyPI Token (Optional)

1. Go to: https://test.pypi.org/
2. Log in (or register if needed)
3. Go to **Account Settings** → **API tokens**
4. Click **"Add API token"**
5. Settings:
   - **Token name**: `super-signal-github-actions-test`
   - **Scope**: "Entire account"
6. Click **"Add token"**
7. **Copy the token** (starts with `pypi-`)

## Step 2: Add Secrets to GitHub

1. Go to your repository: https://github.com/TradingAsBuddies/super-signal
2. Click **Settings** (top right)
3. In left sidebar, click **Secrets and variables** → **Actions**
4. Click **"New repository secret"**

### Add PYPI_API_TOKEN

1. Click **"New repository secret"**
2. **Name**: `PYPI_API_TOKEN`
3. **Secret**: Paste your PyPI token (the long string starting with `pypi-`)
4. Click **"Add secret"**

### Add TEST_PYPI_API_TOKEN (Optional)

1. Click **"New repository secret"**
2. **Name**: `TEST_PYPI_API_TOKEN`
3. **Secret**: Paste your Test PyPI token
4. Click **"Add secret"**

## Step 3: Verify Setup

After adding secrets, you should see them listed (values are hidden):
- ✅ `PYPI_API_TOKEN`
- ✅ `TEST_PYPI_API_TOKEN` (optional)

## Step 4: Test the Workflow

The workflow will now automatically run when you push a tag:

```bash
# Create a test tag
git tag v2.0.1-test
git push --tags

# Or re-run the failed v2.0.0 workflow:
# Go to: https://github.com/TradingAsBuddies/super-signal/actions
# Click the failed workflow
# Click "Re-run failed jobs"
```

## What Happens When Workflow Runs

1. ✅ **Build**: Creates distribution packages
2. ✅ **Test PyPI**: Uploads to https://test.pypi.org (if token configured)
3. ✅ **PyPI**: Uploads to https://pypi.org
4. ✅ **GitHub Release**: Creates release with artifacts

## Troubleshooting

### "Invalid or non-existent authentication information"

- Check that the secret name is exactly: `PYPI_API_TOKEN` (case-sensitive)
- Verify the token starts with `pypi-`
- Make sure you copied the entire token

### "403 Forbidden"

- Token might be for wrong project
- Use "Entire account" scope for first upload
- After first upload, recreate token with "Project: super-signal" scope

### "Project not found"

- You need to upload manually the first time
- Run: `twine upload dist/*`
- Then GitHub Actions will work for future releases

### Workflow Still Failing?

Check the logs:
1. Go to: https://github.com/TradingAsBuddies/super-signal/actions
2. Click the failed workflow run
3. Click the failed job
4. Read error messages

## Security Notes

- ✅ Tokens are encrypted and never displayed after creation
- ✅ Secrets are only available to workflows in your repository
- ✅ Use project-scoped tokens (not account-scoped) after first upload
- ❌ Never commit tokens to git
- ❌ Never share tokens publicly

## Alternative: Trusted Publishing (More Secure)

For even better security, you can use PyPI's Trusted Publishing (no tokens needed):

1. First, publish once manually with token
2. Go to: https://pypi.org/manage/project/super-signal/settings/publishing/
3. Add trusted publisher:
   - **Owner**: `TradingAsBuddies`
   - **Repository name**: `super-signal`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`
4. Update workflow to use `id-token: write` permission (I can help with this)

## Need Help?

Contact: David Duncan <tradingasbuddies@davidduncan.org>
