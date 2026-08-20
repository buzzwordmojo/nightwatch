Text and password input. Password fields pair a Lock leading icon with an Eye/EyeOff toggle; validation copy sits below in 12px red.

```jsx
<TextField type="password" value={pw} onChange={setPw} leadingIcon={<Lock size={16}/>}
  trailingIcon={<Eye size={16}/>} onTrailingClick={toggle} error="Password must be at least 8 characters" />
```
