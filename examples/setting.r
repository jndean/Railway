

func F(x)
  do x *= 2
  let y = x * 3
  do x += y
return x

func G()
  let x = 0

  let i = 0
  loop i = 0
    do x += i
    do i += 1
  until i = 5
  unlet i = 5

  for i = 0
    do x += i
  step i += 1
  until i = 5

cpreturn x


func STEP (val1 val2 step thresh)
  try scale = 1 , 1/2 , 1/3
    do step *= scale
    do val1 += step
    do val2 += step
    if val1 < val2
      catch ((val1 / val2) - 1) < thresh
    else
      catch ((val2 / val1) - 1) < thresh
    fi val1 < val2
  otherwise 
return scale

    
func main(argc argv[])
  let x = 1
  let y = 2
  do x += y
  do x += 2 * (y + 1)
  unlet x = 7
  unlet y = 2

  call x = G{}

return

