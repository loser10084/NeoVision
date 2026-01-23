<script>
export default {
  onLaunch() {
    console.log('SmartImage App Launch')
  }
}
</script>

<style>
  /* 全局黑白极简基调，贴近 iOS 医疗工具的清爽气质 */
  page {
    background-color: #f7f7f8;
    color: #0c0d0f;
    font-family: "SF Pro Display", "SF Pro Text", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
    letter-spacing: 0.15rpx;
    -webkit-font-smoothing: antialiased;
  }

  .safe-area {
    padding: 34rpx 30rpx 26rpx;
  }

  .card {
    background: #ffffff;
    border: 1rpx solid #e6e7eb;
    border-radius: 28rpx;
    padding: 30rpx;
    box-shadow: 0 22rpx 60rpx rgba(0, 0, 0, 0.04);
  }

  .section-title {
    font-size: 34rpx;
    font-weight: 650;
    letter-spacing: 0.4rpx;
    margin-bottom: 18rpx;
    color: #0c0d0f;
  }

  .subtle {
    color: #5e616a;
  }

  .action-bar {
    display: flex;
    gap: 16rpx;
    margin-top: 18rpx;
  }

  .divider {
    height: 1rpx;
    background: linear-gradient(90deg, transparent, #e6e7eb, transparent);
    margin: 24rpx 0;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 10rpx;
    padding: 14rpx 20rpx;
    border-radius: 999rpx;
    background: #f3f4f6;
    color: #0c0d0f;
    border: 1rpx solid #e6e7eb;
  }

  .eyebrow {
    font-size: 26rpx;
    color: #6a6f78;
    letter-spacing: 0.6rpx;
    text-transform: uppercase;
  }

  /* Wot Design 组件的全局极简黑白风覆盖 */
  :deep(.wd-button--primary) {
    background: #ffffff;
    border-color: #0f1012;
    color: #0f1012;
    box-shadow: none;
  }

  :deep(.wd-button--primary.is-plain) {
    background: #ffffff;
    color: #0f1012;
    border-color: #0f1012;
    box-shadow: none;
  }

  :deep(.wd-button--default.is-plain) {
    background: #ffffff;
    color: #0c0d0f;
    border-color: #d8dade;
  }

  :deep(.wd-tag) {
    border-radius: 999rpx;
    font-weight: 600;
  }

  :deep(.wd-tag--plain.wd-tag--primary) {
    color: #0f1012;
    border-color: #0f1012;
    background: #ffffff;
  }

  :deep(.wd-tag--plain.wd-tag--success) {
    color: #1f8b4c;
    border-color: #1f8b4c;
    background: #ffffff;
  }

  :deep(.wd-tag--plain.wd-tag--warning) {
    color: #c68a15;
    border-color: #c68a15;
    background: #ffffff;
  }

  :deep(.wd-tag--plain.wd-tag--info) {
    color: #5e616a;
    border-color: #d8dade;
    background: #ffffff;
  }

  :deep(.wd-search) {
    background: #ffffff;
    border-radius: 999rpx;
    border: 1rpx solid #e6e7eb;
    padding: 4rpx 8rpx;
  }

  :deep(.wd-search__input) {
    background: transparent;
  }

  :deep(.wd-cell) {
    background: #ffffff;
  }

  :deep(.wd-cell__title) {
    color: #0c0d0f;
    font-weight: 600;
  }

  :deep(.wd-cell__label) {
    color: #6a6f78;
  }

  :deep(.wd-form-item__label) {
    color: #111318;
    font-weight: 600;
  }

  :deep(.wd-input) {
    background: #ffffff;
    border: 1rpx solid #dee0e5;
    border-radius: 18rpx;
    padding: 0 16rpx;
    color: #0c0d0f;
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

  /* 保留校验提示空间，避免输入框被顶开 */
  :deep(.wd-form-item__message) {
    min-height: 32rpx;
    margin-top: 6rpx;
    line-height: 32rpx;
    display: block;
  }

  /* 给每个表单项额外底部留白，错误提示不会挤压输入框 */
  :deep(.wd-form-item) {
    margin-bottom: 12rpx;
  }

  :deep(.wd-form-item__content) {
    align-items: center;
  }
</style>
