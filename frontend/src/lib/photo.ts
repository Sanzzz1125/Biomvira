/**
 * Phone photos are shrunk in the browser before upload: the long side becomes at most 2,600 px (the size the server
 * reads at) and the photo is saved as JPEG. A 12-50 MP camera photo becomes about 1 MB, so it uploads quickly and
 * stays inside the server's limits. The browser applies the photo's EXIF rotation while drawing it.
 * PDFs and small images are sent as they are; if the browser cannot read the image, the original is sent.
 */
export const MAX_PHOTO_SIDE = 2600;
export const MAX_PHOTO_BYTES = 30 * 1024 * 1024;

export async function preparePhoto(file: File): Promise<File> {
  if (!/\.(jpe?g|png)$/i.test(file.name) || typeof createImageBitmap !== 'function') return file;
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' } as ImageBitmapOptions);
    const scale = Math.min(1, MAX_PHOTO_SIDE / Math.max(bitmap.width, bitmap.height));
    if (scale === 1 && file.size <= 3 * 1024 * 1024) {
      bitmap.close();
      return file;
    }
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const ctx = canvas.getContext('2d');
    if (!ctx) return file;
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9));
    if (!blob) return file;
    return new File([blob], file.name.replace(/\.(jpe?g|png)$/i, '.jpg'), { type: 'image/jpeg' });
  } catch {
    return file;
  }
}
