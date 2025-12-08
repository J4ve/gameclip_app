# Firestore Index Configuration

The metadata preset functionality requires a composite index in Firestore:

## Required Index

**Collection:** `metadata_presets`

**Fields to index:**
1. `user_id` (Ascending)
2. `created_at` (Descending)

## How to Create the Index

When you run the integration tests, Firebase will provide a URL to create the required index.

Alternatively, you can create it manually in the Firebase Console:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: `video-merger-edc29`
3. Navigate to: **Firestore Database** → **Indexes** → **Composite**
4. Click **Create Index**
5. Configure:
   - Collection ID: `metadata_presets`
   - Fields:
     - `user_id` - Ascending
     - `created_at` - Descending
   - Query scopes: Collection
6. Click **Create**

The index will take a few minutes to build. Once completed, the integration tests will pass.

## firestore.indexes.json

For automated deployment, add this to your `firestore.indexes.json`:

```json
{
  "indexes": [
    {
      "collectionGroup": "metadata_presets",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "user_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "created_at",
          "order": "DESCENDING"
        }
      ]
    }
  ]
}
```
