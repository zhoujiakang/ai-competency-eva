/**
 * 输入法（IME）正在拼字时，回车属于"确认候选词"，不能当成提交。
 *
 * Chrome 在组字过程中的 keydown 上会把 isComposing 置为 true；
 * Safari 与部分 Firefox 版本不给 isComposing，而是给 keyCode 229。
 * 两者都要判断，否则中文输入法按一次回车就会把拼音直接发出去。
 */
export const isImeComposing = (event) =>
  event?.nativeEvent?.isComposing === true || event?.isComposing === true || event?.keyCode === 229;
