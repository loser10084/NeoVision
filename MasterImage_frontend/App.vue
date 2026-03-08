<script>
export default {
  onLaunch() {
    console.log('SmartImage App Launch')
  }
}
</script>

<style>
  page {
    --mi-primary: #2f78d8;
    --mi-primary-strong: #245eac;
    --mi-primary-soft: #eaf3ff;
    --mi-text-main: #143356;
    --mi-text-regular: #2f4f73;
    --mi-text-muted: #6a84a6;
    --mi-bg: #edf4ff;
    --mi-bg-soft: #f5f9ff;
    --mi-surface: #ffffff;
    --mi-border: #d6e5f7;
    --mi-border-strong: #bfd5ef;
    --mi-shadow: 0 20rpx 56rpx rgba(45, 113, 194, 0.1);
    --mi-radius-card: 28rpx;
    --mi-radius-field: 18rpx;
    --mi-radius-pill: 999rpx;
    background:
      radial-gradient(700rpx 360rpx at -8% -4%, rgba(136, 186, 255, 0.22), transparent 68%),
      radial-gradient(560rpx 300rpx at 106% 3%, rgba(168, 207, 255, 0.2), transparent 64%),
      linear-gradient(180deg, #f4f8ff 0%, #edf4ff 34%, #e9f2ff 100%);
    background-color: var(--mi-bg);
    color: var(--mi-text-main);
    font-family: "Avenir Next", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
    letter-spacing: 0.1rpx;
    -webkit-font-smoothing: antialiased;
  }

  .page {
    min-height: 100vh;
    color: var(--mi-text-main);
  }

  .safe-area {
    padding: 34rpx 30rpx 28rpx;
  }

  .card {
    background: #ffffff;
    border: 1rpx solid var(--mi-border);
    border-radius: var(--mi-radius-card);
    padding: 30rpx;
    box-shadow: var(--mi-shadow);
    backdrop-filter: blur(2rpx);
  }

  .section-title {
    font-size: 34rpx;
    font-weight: 650;
    letter-spacing: 0.2rpx;
    margin-bottom: 18rpx;
    color: var(--mi-text-main);
  }

  .subtle {
    color: var(--mi-text-muted);
  }

  .action-bar {
    display: flex;
    gap: 16rpx;
    margin-top: 18rpx;
    justify-content: space-between;
    align-items: stretch;
  }

  .action-bar:not(.column) > * {
    flex: 1 1 0;
    min-width: 0;
  }

  .action-bar.column > * {
    width: 100%;
  }

  .divider {
    height: 1rpx;
    background: linear-gradient(90deg, transparent, var(--mi-border-strong), transparent);
    margin: 24rpx 0;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 10rpx;
    padding: 14rpx 20rpx;
    border-radius: var(--mi-radius-pill);
    background: var(--mi-primary-soft);
    color: var(--mi-primary-strong);
    border: 1rpx solid var(--mi-border);
  }
  .mi-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 0;
    box-sizing: border-box;
  }

  .eyebrow {
    font-size: 26rpx;
    color: var(--mi-text-muted);
    letter-spacing: 0.5rpx;
    text-transform: uppercase;
  }

  :deep(.wd-button) {
    border-radius: 999rpx;
  }

  :deep(.wd-button--primary) {
    background: linear-gradient(135deg, var(--mi-primary) 0%, var(--mi-primary-strong) 100%);
    border-color: transparent;
    color: #ffffff;
    box-shadow: 0 10rpx 28rpx rgba(47, 120, 216, 0.28);
  }

  :deep(.wd-button--primary.is-plain) {
    background: var(--mi-primary-soft);
    color: var(--mi-primary-strong);
    border-color: var(--mi-border-strong);
    box-shadow: none;
  }

  :deep(.wd-button--default.is-plain) {
    background: #ffffff;
    color: var(--mi-text-regular);
    border-color: var(--mi-border);
  }

  :deep(.wd-tag) {
    border-radius: 999rpx;
    font-weight: 600;
  }

  :deep(.wd-tag--plain.wd-tag--primary) {
    color: var(--mi-primary-strong);
    border-color: var(--mi-border-strong);
    background: var(--mi-primary-soft);
  }

  :deep(.wd-tag--plain.wd-tag--success) {
    color: #1f8b4c;
    border-color: #bce2cb;
    background: #f3fbf6;
  }

  :deep(.wd-tag--plain.wd-tag--warning) {
    color: #b27613;
    border-color: #f2dfbe;
    background: #fdf8ef;
  }

  :deep(.wd-tag--plain.wd-tag--info) {
    color: var(--mi-text-muted);
    border-color: var(--mi-border);
    background: #f8fbff;
  }

  :deep(.wd-search) {
    background: #ffffff;
    border-radius: 999rpx;
    border: 1rpx solid var(--mi-border);
    padding: 4rpx 8rpx;
  }

  :deep(.wd-search__input) {
    background: transparent;
  }

  :deep(.wd-cell) {
    background: transparent;
  }

  :deep(.wd-cell__title) {
    color: var(--mi-text-main);
    font-weight: 600;
  }

  :deep(.wd-cell__label) {
    color: var(--mi-text-muted);
  }

  :deep(.wd-form-item__label) {
    color: var(--mi-text-main);
    font-weight: 600;
  }

  :deep(.wd-input) {
    background: #ffffff;
    border: 1rpx solid var(--mi-border);
    border-radius: var(--mi-radius-field);
    padding: 0 16rpx;
    color: var(--mi-text-main);
    min-height: 80rpx;
    display: flex;
    align-items: center;
    box-sizing: border-box;
  }

  :deep(.wd-input__inner) {
    font-size: 30rpx;
    line-height: normal;
    height: auto;
    padding: 0;
  }

  :deep(.wd-form-item__message) {
    min-height: 32rpx;
    margin-top: 6rpx;
    line-height: 32rpx;
    display: block;
  }

  :deep(.wd-form-item) {
    margin-bottom: 12rpx;
  }

  :deep(.wd-form-item__content) {
    align-items: center;
  }
</style>

